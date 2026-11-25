-- TRECHO de projeto/jogo/servidor/sql/21_golpes.sql, linhas 125–236 (recorte público da DCC061).
-- Mostra a Decisão 1: a jogada é validada num gatilho do PostgreSQL, com travas de linha
-- (FOR UPDATE) contra jogadas simultâneas e recusa identificada pelo código da regra (RNxx).
-- O restante da função (aplicação do efeito) e as demais migrações ficam no repositório completo.

-- RN12, RN13, RN15, RN16, RN18, RN21 (12_itens.sql) + v3: carta com padrão não aplica nada aqui —
-- valida e consome como sempre, guarda o valor por alvo em NEW.base e libera a transação para os
-- alvos (mapas.golpe = id da jogada); o efeito vem da soma de jogada_alvo. Sem padrão, igual à v2
-- (área em losango, PvP ×2 e grupos do 16_pvpve.sql, cura até vida_max do 15_progressao.sql).
CREATE OR REPLACE FUNCTION fn_processar_jogada() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    v_partida   partida%ROWTYPE;
    v_lancador  participacao%ROWTYPE;
    v_item      item%ROWTYPE;
    v_municao   item%ROWTYPE;
    v_carta     carta%ROWTYPE;
    v_classe    classe%ROWTYPE;
    v_extra     integer := 0;      -- bônus da munição + nível do item
    v_bonus     integer := 0;      -- bônus de classe (RN18)
    v_alcance   integer;
    v_distancia integer;
    v_base      integer;
    v_valor     integer;
    v_total     integer := 0;
    v_atingidos integer := 0;
    v_depois    integer;
    v_pvp       boolean;       -- Mapa do Chefe (16_pvpve.sql): PvP entre grupos
    c_mult_pvp  CONSTANT integer := 2;   -- golpe em jogador dói o dobro (pvpve.MULT_PVP): com 100–200 de
                                         -- vida, sem isso uma luta entre grupos levaria 10 rodadas
    v_feridos   text := '';    -- jogadores de outro grupo feridos e de pé (efeito da carta, 16)
    r           record;
BEGIN
    SELECT * INTO v_partida FROM partida WHERE id = NEW.partida_id;
    v_pvp := v_partida.modo = 'PVPVE';
    IF v_partida.situacao IS DISTINCT FROM 'EM_ANDAMENTO' THEN
        RAISE EXCEPTION 'RN13: a partida % não está em andamento', NEW.partida_id
              USING ERRCODE = 'integrity_constraint_violation';
    END IF;
    IF v_partida.fase <> 'JOGADORES' THEN
        RAISE EXCEPTION 'RN15: agora é a vez dos inimigos; espere a próxima rodada'
              USING ERRCODE = 'integrity_constraint_violation';
    END IF;

    SELECT * INTO v_lancador FROM participacao
    WHERE partida_id = NEW.partida_id AND jogador_id = NEW.jogador_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'RN13: o jogador % não participa da partida %', NEW.jogador_id, NEW.partida_id
              USING ERRCODE = 'integrity_constraint_violation';
    END IF;
    IF v_lancador.vida = 0 THEN
        RAISE EXCEPTION 'RN13: você está abatido e não pode usar itens'
              USING ERRCODE = 'integrity_constraint_violation';
    END IF;
    IF v_lancador.acoes < 1 THEN
        RAISE EXCEPTION 'RN16: você já usou as 2 ações desta rodada'
              USING ERRCODE = 'integrity_constraint_violation';
    END IF;

    -- RN12: o item precisa estar na MOCHILA de quem usa (só a carta: 1ª instância dela)
    IF NEW.item_id IS NULL THEN
        SELECT * INTO v_item FROM item
        WHERE jogador_id = NEW.jogador_id AND local = 'MOCHILA' AND carta_id = NEW.carta_id
        ORDER BY id LIMIT 1 FOR UPDATE;
    ELSE
        SELECT * INTO v_item FROM item WHERE id = NEW.item_id FOR UPDATE;
    END IF;
    IF NOT FOUND OR v_item.jogador_id IS DISTINCT FROM NEW.jogador_id OR v_item.local <> 'MOCHILA' THEN
        RAISE EXCEPTION 'RN12: esse item não está na sua mochila'
              USING ERRCODE = 'integrity_constraint_violation';
    END IF;
    NEW.item_id := v_item.id;
    NEW.carta_id := v_item.carta_id;
    SELECT * INTO v_carta FROM carta WHERE id = v_item.carta_id;
    IF v_carta.tipo_item = 'TESOURO' THEN
        RAISE EXCEPTION 'RN12: "%" é tesouro: não se usa, se vende', v_carta.nome
              USING ERRCODE = 'integrity_constraint_violation';
    END IF;
    IF v_carta.tipo_item = 'MUNICAO' THEN
        RAISE EXCEPTION 'RN21: "%" é munição: dispare com uma arma de %', v_carta.nome, lower(v_carta.municao)
              USING ERRCODE = 'integrity_constraint_violation';
    END IF;

    -- RN21: arma à distância exige munição da família (escolhida, ou a de menor bônus)
    NEW.municao_id := CASE WHEN v_carta.municao IS NULL THEN NULL ELSE NEW.municao_id END;
    NEW.municao_carta_id := NULL;
    IF v_carta.municao IS NOT NULL THEN
        SELECT i.* INTO v_municao
        FROM item i JOIN carta c ON c.id = i.carta_id JOIN carta_ataque ca ON ca.carta_id = c.id
        WHERE i.jogador_id = NEW.jogador_id AND i.local = 'MOCHILA' AND c.tipo_item = 'MUNICAO'
          AND c.municao = v_carta.municao AND (NEW.municao_id IS NULL OR i.id = NEW.municao_id)
        ORDER BY ca.dano, i.quantidade, i.id
        LIMIT 1 FOR UPDATE OF i;
        IF NOT FOUND AND NEW.municao_id IS NOT NULL THEN
            RAISE EXCEPTION 'RN21: essa munição não serve em "%" (precisa de %)', v_carta.nome, lower(v_carta.municao)
                  USING ERRCODE = 'integrity_constraint_violation';
        ELSIF NOT FOUND THEN
            RAISE EXCEPTION 'RN21: sem munição: "%" precisa de % na mochila', v_carta.nome, lower(v_carta.municao)
                  USING ERRCODE = 'integrity_constraint_violation';
        END IF;
        NEW.municao_id := v_municao.id;
        NEW.municao_carta_id := v_municao.carta_id;
        SELECT dano INTO v_extra FROM carta_ataque WHERE carta_id = v_municao.carta_id;
    END IF;
    v_extra := v_extra + v_item.nivel;

    SELECT * INTO v_classe FROM classe WHERE id = v_lancador.classe_id;
    v_alcance := v_carta.alcance;
    IF v_classe.categoria_bonus = v_carta.categoria THEN                        -- RN18
        v_bonus := v_classe.bonus_efeito;
        v_alcance := v_alcance + v_classe.bonus_alcance;
    END IF;
    v_distancia := abs(NEW.alvo_x - v_lancador.x) + abs(NEW.alvo_y - v_lancador.y);
    IF v_distancia > v_alcance THEN
        RAISE EXCEPTION 'RN13: o alvo está a % tiles; "%" alcança %', v_distancia, v_carta.nome, v_alcance
              USING ERRCODE = 'integrity_constraint_violation';
    END IF;
    -- … (continua no repositório completo)
