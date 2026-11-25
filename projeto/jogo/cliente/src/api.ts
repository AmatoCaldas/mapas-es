import type { Classe, PartidaAberta, Regiao, Sessao } from "./tipos";
import type { EstadoMochila } from "./tipos";
import type { Item } from "./tipos";
import type { ResultadoJogador, Sessao3 } from "./tipos";

// Sessão por aba (sessionStorage): duas abas = dois jogadores, útil para testar o co-op.
const CHAVE = "mapas.sessao";

export function sessao(): Sessao | null {
  const s = sessionStorage.getItem(CHAVE);
  return s ? (JSON.parse(s) as Sessao) : null;
}
export function guardarSessao(s: Sessao | null): void {
  if (s) sessionStorage.setItem(CHAVE, JSON.stringify(s));
  else sessionStorage.removeItem(CHAVE);
}

/** Único ponto do cliente que faz HTTP (regra em src/arquitetura.teste.mjs): token, JSON e erro do servidor. */
export async function pedir<T>(metodo: string, caminho: string, corpo?: unknown): Promise<T> {
  const s = sessao();
  const r = await fetch(caminho, {
    method: metodo,
    headers: { "Content-Type": "application/json", ...(s ? { Authorization: `Bearer ${s.token}` } : {}) },
    body: corpo ? JSON.stringify(corpo) : undefined,
  });
  const dados = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(dados.erro ?? dados.detail ?? `erro ${r.status}`);
  return dados as T;
}

export const api = {
  login: (email: string, senha: string) => pedir<Sessao>("POST", "/api/login", { email, senha }),
  cadastro: (apelido: string, email: string, senha: string) => pedir<Sessao>("POST", "/api/cadastro", { apelido, email, senha }),
  lobby: () => pedir<{ partidas: PartidaAberta[]; classes: Classe[]; regioes: Regiao[]; partida_atual: number | null }>("GET", "/api/lobby"),
  criar: (regiao_id: number, classe_id: number) => pedir<{ partida_id: number }>("POST", "/api/partidas", { regiao_id, classe_id }),
  entrar: (partida: number, classe_id: number) => pedir<{ partida_id: number }>("POST", `/api/partidas/${partida}/entrar`, { classe_id }),
};

// ----- v2 · mochila e baú (pacote C; rotas do pacote B, contrato em ARQUITETURA_V2.md §3) -----
type LocalMover = "MOCHILA" | "BAU" | "BOLSO";
/** Rotação da v3 em passos de 90° no sentido horário (mochila/forma.ts). */
export type RotacaoMover = 0 | 1 | 2 | 3;

export const apiMochila = {
  estado: () => pedir<EstadoMochila>("GET", "/api/mochila"),
  /** `rotacao` é da v3; `girado` (rotação ímpar) vai junto para o servidor da v2, que só gira 90°. */
  mover: (item: number, local: LocalMover, x?: number, y?: number, rotacao?: RotacaoMover) =>
    pedir<EstadoMochila>("POST", "/api/mochila/mover",
      rotacao === undefined ? { item, local, x, y } : { item, local, x, y, rotacao, girado: rotacao % 2 === 1 }),
  combinar: (item: number, alvo: number) => pedir<EstadoMochila>("POST", "/api/mochila/combinar", { item, alvo }),
  descartar: (item: number) => pedir<EstadoMochila>("POST", "/api/mochila/descartar", { item }),
  catalogo: () => pedir<{ cartas: Record<string, unknown>[]; receitas?: { carta_a: number; carta_b: number; resultado: number }[] }>(
    "GET", "/api/catalogo/itens"),
};

// ------------------------------------------------------------------ v2 · interface (pacote G)
export type ModoNovaPartida = "MASMORRA" | "CLASSICO";
export interface NovaPartida {
  regiao_id: number; classe_id: number;
  segundos_turno: number;      // 0 = sem limite (11_turno.sql, pacote A); servidores antigos ignoram
  modo: ModoNovaPartida;       // MASMORRA só vale na onda 2; até lá o servidor ignora e cria a clássica
}
export interface EstatisticasPerfil {
  partidas: number; vitorias: number; derrotas: number; abandonadas: number; em_andamento: number;
  taxa_vitoria: number; dano: number; cura: number; bloqueio: number; abates: number; jogadas: number; maior_rodada: number;
}
export interface PartidaPerfil {
  partida_id: number; regiao_id: number; regiao: string; situacao: string; inicio: string | null; termino: string | null;
  rodadas: number; classe_id: number | null; classe: string | null; vida_final: number;
  jogadas: number; dano: number; cura: number; bloqueio: number; abates: number;
}
/** GET /api/perfil e /api/perfil/{apelido} (17_perfil.sql). Nível/XP são provisórios até a progressão (onda 2). */
export interface Perfil {
  jogador: { id: number; apelido: string; desde: string | null };
  classe_favorita: { id: number; nome: string; partidas: number; vitorias: number; estimada: boolean } | null;
  progresso: { nivel: number; xp: number; xp_nivel: number; xp_proximo: number; provisorio: boolean };
  estatisticas: EstatisticasPerfil;
  carta_favorita: { carta_id: number; nome: string; categoria: string; usos: number; efeito_total: number } | null;
  historico: PartidaPerfil[];
}

export const criarPartida = (dados: NovaPartida) => pedir<{ partida_id: number }>("POST", "/api/partidas", dados);
export const buscarPerfil = (apelido?: string) =>
  pedir<Perfil>("GET", apelido ? `/api/perfil/${encodeURIComponent(apelido)}` : "/api/perfil");

// ------------------------------------------------------------------ v2 · progressão e Mercador (pacote P)
// Rotas em servidor/main.py; regras e preços em servidor/sql/15_progressao.sql.
export interface RegiaoNivel { id: number; nome: string; nivel_minimo: number; liberada: boolean; }
/** GET /api/progresso. xp_nivel / xp_proximo = barra do nível atual; vida_max = vida na próxima partida. */
export interface Progresso {
  nivel: number; xp: number; xp_nivel: number; xp_proximo: number; ouro: number;
  vida_max: number; regioes: RegiaoNivel[];
}
/** Uma carta à venda hoje (`lote` = quantas unidades vêm por compra; munição vem em meia pilha). */
export interface OfertaMercador {
  carta_id: number; nome: string; descricao: string; categoria: Item["categoria"]; tipo_item: Item["tipo_item"];
  raridade: Item["raridade"]; icone: string; largura: number; altura: number; empilha: number; valor: number;
  alcance: number; area: number; municao: string | null; efeito: Item["efeito"];
  lote: number; preco: number; preco_cheio: number; oferta: boolean;
}
/** Quanto um item do jogador vale na venda (pilha inteira) e quanto custa o próximo nível (só armas). */
export interface PrecoItem { item_id: number; venda: number; melhoria: number | null; }
export type TipoAmpliacao = "MOCHILA" | "BAU" | "BOLSO";
export interface AmpliacaoMercador {
  tipo: TipoAmpliacao; atual: string; proxima: string | null; custo: number | null; nivel_minimo: number | null; liberada: boolean;
}
export interface TransacaoMercador {
  motivo: "COMPRA" | "VENDA" | "MELHORIA" | "AMPLIACAO"; ouro: number;
  carta?: string; quantidade?: number; destino?: string; nivel?: number; tipo?: TipoAmpliacao; passo?: number;
}
/** GET /api/mercador e resposta de todo POST /api/mercador/* (com `transacao` nos POST). */
export interface EstadoMercador {
  progresso: Progresso; ouro: number; dia: string; renova_em: string; em_partida: boolean;
  estoque: OfertaMercador[]; precos: PrecoItem[]; ampliacoes: AmpliacaoMercador[];
  mochila: EstadoMochila & { tem_bolso?: boolean };
  transacao?: TransacaoMercador;
}

export const buscarProgresso = () => pedir<Progresso>("GET", "/api/progresso");
export const apiMercador = {
  ver: () => pedir<EstadoMercador>("GET", "/api/mercador"),
  comprar: (carta: number) => pedir<EstadoMercador>("POST", "/api/mercador/comprar", { carta }),
  vender: (item: number, quantidade?: number) => pedir<EstadoMercador>("POST", "/api/mercador/vender", { item, quantidade }),
  melhorar: (item: number) => pedir<EstadoMercador>("POST", "/api/mercador/melhorar", { item }),
  ampliar: (tipo: TipoAmpliacao) => pedir<EstadoMercador>("POST", "/api/mercador/ampliar", { tipo }),
};

// ------------------------------------------------------------------ v3 · sessão (pacote S1)
// Volta obrigatória, desistir e bloqueio por abandono (RN50). Regras em servidor/sql/19_sessao.sql.
/** POST /api/partidas/{id}/desistir: o loot em risco virou saco no tile; `situacao` é a da partida depois disso. */
export interface Desistencia {
  jogador: number; situacao: string; apelido?: string; x?: number; y?: number; itens_no_saco?: number;
}
export const apiSessao = {
  ver: () => pedir<Sessao3>("GET", "/api/sessao"),
  desistir: (partida: number) => pedir<Desistencia>("POST", `/api/partidas/${partida}/desistir`, {}),
};
// Perfil: abandonos (partidas que acabaram com você fora) e a taxa sobre as partidas concluídas, em %.
export interface EstatisticasPerfil { abandonos?: number; desistencias?: number; taxa_abandono?: number; }
export interface PartidaPerfil { resultado?: ResultadoJogador; }
