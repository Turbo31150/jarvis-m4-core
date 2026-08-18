-- board — conseil d'experts local souverain. Schema SQLite.
--
-- SEPT objets, pas un de plus. Les quatre premiers sont ceux du cahier des
-- charges ; les trois derniers (queries, answers, citations) sont INFERES de la
-- mission « N experts repondent en citant, puis une synthese arbitre » — le
-- prompt d'origine etait tronque a cet endroit. A revoir si l'intention differe.
--
-- Choix de stockage (PHASE 0) : pgvector absent des deux containers Postgres
-- (0 sur 61 extensions) ET independance exigee vis-a-vis de la prod.
-- Donc SQLite + FTS5 + embeddings BLOB numpy float32, cosine en Python.
-- Dimension CONSTATEE : 768 (text-embedding-nomic-embed-text-v1.5, LM Studio
-- :1234, stable sur 3 appels). Aucune dimension supposee.

PRAGMA journal_mode = WAL;          -- lectures concurrentes pendant l'ingestion
PRAGMA foreign_keys = ON;

-- 1. DOMAINS ---------------------------------------------------------------
-- `experts[]` du cahier des charges n'est PAS materialise en colonne : la
-- relation vit dans experts.domain_id. Un tableau d'ids dupliquerait la source
-- de verite et divergerait a la premiere suppression.
CREATE TABLE IF NOT EXISTS domains (
    id            TEXT PRIMARY KEY,
    display_name  TEXT NOT NULL,
    description   TEXT,
    query_count   INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 2. EXPERTS ---------------------------------------------------------------
-- `lens` EST le system prompt, redige a la 1re personne. C'est le coeur du
-- board : deux experts qui partagent la meme lens votent deux fois pour la
-- meme chose et fabriquent un faux consensus.
CREATE TABLE IF NOT EXISTS experts (
    id            TEXT PRIMARY KEY,
    domain_id     TEXT NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    display_name  TEXT NOT NULL,
    lens          TEXT NOT NULL,
    bio           TEXT,
    is_arbitre    INTEGER NOT NULL DEFAULT 0,   -- 1 = rend la synthese
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_experts_domain ON experts(domain_id);

-- 3. SOURCES ---------------------------------------------------------------
-- content_sha256 UNIQUE : re-ingerer le meme fichier ne duplique rien.
-- expert_id nullable — une source peut nourrir tout un domaine.
CREATE TABLE IF NOT EXISTS sources (
    id             TEXT PRIMARY KEY,
    domain_id      TEXT NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    expert_id      TEXT REFERENCES experts(id) ON DELETE SET NULL,
    kind           TEXT NOT NULL CHECK (kind IN ('pdf','blog','transcript','md','repo')),
    title          TEXT NOT NULL,
    authors        TEXT,                         -- JSON array
    year           INTEGER,
    url            TEXT,
    local_path     TEXT,
    content_sha256 TEXT NOT NULL UNIQUE,
    ingested_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sources_domain ON sources(domain_id);

-- 4. CHUNKS ----------------------------------------------------------------
-- embedding : BLOB = numpy float32 brut, 768 * 4 = 3072 octets. embedding_dim
-- est stocke pour que le code REFUSE de comparer deux dimensions differentes
-- plutot que de rendre un cosine silencieusement faux.
CREATE TABLE IF NOT EXISTS chunks (
    id             TEXT PRIMARY KEY,
    source_id      TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    domain_id      TEXT NOT NULL,
    expert_id      TEXT,
    chunk_idx      INTEGER NOT NULL,
    text           TEXT NOT NULL,
    token_count    INTEGER,
    embedding      BLOB,                          -- NULL = pas encore vectorise
    embedding_dim  INTEGER,
    embedding_model TEXT,
    UNIQUE (source_id, chunk_idx)
);
CREATE INDEX IF NOT EXISTS idx_chunks_domain ON chunks(domain_id);
CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_id);

-- Index plein-texte. `content=` le lie a chunks : pas de duplication du texte.
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    text,
    content='chunks',
    content_rowid='rowid',
    tokenize="unicode61 remove_diacritics 2"     -- « resume » trouve « résumé »
);
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, text) VALUES (new.rowid, new.text);
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES('delete', old.rowid, old.text);
END;
CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES('delete', old.rowid, old.text);
    INSERT INTO chunks_fts(rowid, text) VALUES (new.rowid, new.text);
END;

-- 5. QUERIES (infere) ------------------------------------------------------
CREATE TABLE IF NOT EXISTS queries (
    id          TEXT PRIMARY KEY,
    domain_id   TEXT NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    question    TEXT NOT NULL,
    asked_at    TEXT NOT NULL DEFAULT (datetime('now')),
    retrieval   TEXT                               -- JSON : mode, k, scores
);

-- 6. ANSWERS (infere) ------------------------------------------------------
-- Une ligne par expert. La synthese est l'answer de l'expert is_arbitre=1,
-- pas une 8e table : elle obeit aux memes regles de citation.
CREATE TABLE IF NOT EXISTS answers (
    id          TEXT PRIMARY KEY,
    query_id    TEXT NOT NULL REFERENCES queries(id) ON DELETE CASCADE,
    expert_id   TEXT NOT NULL REFERENCES experts(id) ON DELETE CASCADE,
    text        TEXT NOT NULL,
    model       TEXT,
    backend     TEXT,
    latency_ms  INTEGER,
    is_synthese INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (query_id, expert_id)
);
CREATE INDEX IF NOT EXISTS idx_answers_query ON answers(query_id);

-- 7. CITATIONS (infere) ----------------------------------------------------
-- La table qui rend la regle « sans corpus cite, pas de reponse » VERIFIABLE :
-- une answer sans ligne ici est une answer a rejeter. C'est une contrainte
-- controlable en SQL, pas une consigne qu'on espere voir respectee.
CREATE TABLE IF NOT EXISTS citations (
    id          TEXT PRIMARY KEY,
    answer_id   TEXT NOT NULL REFERENCES answers(id) ON DELETE CASCADE,
    chunk_id    TEXT NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    rank        INTEGER,
    score       REAL,
    quoted      TEXT,
    UNIQUE (answer_id, chunk_id)
);
CREATE INDEX IF NOT EXISTS idx_citations_answer ON citations(answer_id);

-- Vue de controle : toute answer sans citation viole la regle fondatrice.
CREATE VIEW IF NOT EXISTS answers_sans_citation AS
SELECT a.id, a.query_id, a.expert_id, substr(a.text, 1, 80) AS extrait
FROM answers a
LEFT JOIN citations c ON c.answer_id = a.id
WHERE c.id IS NULL;
