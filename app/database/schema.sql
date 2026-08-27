-- ============================================================================

-- EXTENSIONS

-- ============================================================================


CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE EXTENSION IF NOT EXISTS vector;


-- ============================================================================

-- USERS

-- ============================================================================


CREATE TABLE users (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),


    username VARCHAR(100) NOT NULL UNIQUE,

    email VARCHAR(255) UNIQUE,


    password_hash VARCHAR(255) NOT NULL,


    role VARCHAR(20) NOT NULL

        CHECK (role IN ('ADMIN', 'USER')),


    status VARCHAR(20) NOT NULL

        CHECK (status IN ('ACTIVE', 'INACTIVE', 'LOCKED')),


    must_change_password BOOLEAN NOT NULL DEFAULT FALSE,


    failed_login_count INTEGER NOT NULL DEFAULT 0,

    locked_until TIMESTAMPTZ,


    last_login_at TIMESTAMPTZ,


    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    deleted_at TIMESTAMPTZ

);


-- ============================================================================

-- LLM CONFIGURATIONS

-- ============================================================================


CREATE TABLE llm_configs (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),


    name VARCHAR(100) NOT NULL UNIQUE,


    provider VARCHAR(30) NOT NULL

        CHECK (

            provider IN (

                'OLLAMA',

                'LOCAL',

                'OPENAI_COMPATIBLE'

            )

        ),


    purpose VARCHAR(30) NOT NULL

        CHECK (

            purpose IN (

                'CHAT',

                'EMBEDDING',

                'PARSING',

                'OKF',

                'ALL'

            )

        ),


    base_url VARCHAR(500),


    model_name VARCHAR(200) NOT NULL,


    encrypted_api_key TEXT,


    embedding_dimension INTEGER,


    settings_json JSONB NOT NULL DEFAULT '{}'::jsonb,


    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    is_default BOOLEAN NOT NULL DEFAULT FALSE,


    created_by UUID REFERENCES users(id),


    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

);


-- ============================================================================

-- DOCUMENTS

-- ============================================================================


CREATE TABLE documents (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),


    owner_id UUID NOT NULL REFERENCES users(id),


    title VARCHAR(500) NOT NULL,

    original_filename VARCHAR(500) NOT NULL,


    mime_type VARCHAR(150) NOT NULL,

    file_extension VARCHAR(20),


    file_size_bytes BIGINT NOT NULL,


    storage_path TEXT NOT NULL,


    file_checksum VARCHAR(64) NOT NULL,


    raw_text TEXT,

    parsed_json JSONB,


    okf_markdown TEXT,

    okf_metadata JSONB,


    status VARCHAR(30) NOT NULL

        CHECK (

            status IN (

                'UPLOADED',

                'PARSING',

                'PARSED',

                'INDEXING',

                'READY',

                'FAILED'

            )

        ),


    parse_status VARCHAR(20) NOT NULL

        CHECK (

            parse_status IN (

                'PENDING',

                'PROCESSING',

                'COMPLETED',

                'FAILED',

                'SKIPPED'

            )

        ),


    index_status VARCHAR(20) NOT NULL

        CHECK (

            index_status IN (

                'PENDING',

                'PROCESSING',

                'COMPLETED',

                'FAILED',

                'SKIPPED'

            )

        ),


    okf_status VARCHAR(20) NOT NULL

        CHECK (

            okf_status IN (

                'PENDING',

                'PROCESSING',

                'COMPLETED',

                'FAILED',

                'SKIPPED'

            )

        ),


    error_message TEXT,


    version INTEGER NOT NULL DEFAULT 1,


    is_active BOOLEAN NOT NULL DEFAULT TRUE,


    llm_config_id UUID REFERENCES llm_configs(id),


    created_by UUID NOT NULL REFERENCES users(id),

    updated_by UUID REFERENCES users(id),


    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    deleted_at TIMESTAMPTZ

);


-- ============================================================================

-- DOCUMENT CHUNKS

-- NOTE:

-- Change VECTOR(1536) if your embedding model uses a different dimension.

-- ============================================================================


CREATE TABLE document_chunks (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),


    document_id UUID NOT NULL

        REFERENCES documents(id)

        ON DELETE CASCADE,


    document_version INTEGER NOT NULL,


    chunk_index INTEGER NOT NULL,


    content TEXT NOT NULL,


    content_hash VARCHAR(64) NOT NULL,


    token_count INTEGER,


    page_number INTEGER,


    section_path TEXT,


    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,


    embedding VECTOR(1536),


    embedding_model VARCHAR(200),


    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    CONSTRAINT uq_document_chunk

        UNIQUE (document_id, document_version, chunk_index)

);


-- ============================================================================

-- PROCESSING JOBS

-- ============================================================================


CREATE TABLE processing_jobs (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),


    document_id UUID NOT NULL

        REFERENCES documents(id)

        ON DELETE CASCADE,


    job_type VARCHAR(30) NOT NULL

        CHECK (

            job_type IN (

                'PARSE',

                'GENERATE_OKF',

                'CHUNK',

                'EMBED',

                'INDEX',

                'DELETE_INDEX'

            )

        ),


    status VARCHAR(20) NOT NULL

        CHECK (

            status IN (

                'QUEUED',

                'RUNNING',

                'COMPLETED',

                'FAILED',

                'CANCELLED'

            )

        ),


    progress_percentage INTEGER NOT NULL DEFAULT 0

        CHECK (

            progress_percentage >= 0

            AND progress_percentage <= 100

        ),


    attempt_count INTEGER NOT NULL DEFAULT 0,


    request_payload JSONB,

    result_payload JSONB,


    error_code VARCHAR(100),

    error_message TEXT,


    llm_config_id UUID REFERENCES llm_configs(id),


    started_at TIMESTAMPTZ,

    completed_at TIMESTAMPTZ,


    created_by UUID NOT NULL REFERENCES users(id),


    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()

);


-- ============================================================================

-- CONVERSATIONS

-- ============================================================================


CREATE TABLE conversations (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),


    user_id UUID NOT NULL REFERENCES users(id),


    title VARCHAR(300) NOT NULL,


    llm_config_id UUID REFERENCES llm_configs(id),


    scope_json JSONB NOT NULL DEFAULT '{}'::jsonb,


    system_prompt TEXT,


    status VARCHAR(20) NOT NULL

        CHECK (

            status IN (

                'ACTIVE',

                'ARCHIVED',

                'DELETED'

            )

        ),


    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    deleted_at TIMESTAMPTZ

);


-- ============================================================================

-- MESSAGES

-- ============================================================================


CREATE TABLE messages (

    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),


    conversation_id UUID NOT NULL

        REFERENCES conversations(id)

        ON DELETE CASCADE,


    parent_message_id UUID

        REFERENCES messages(id),


    role VARCHAR(20) NOT NULL

        CHECK (

            role IN (

                'USER',

                'ASSISTANT',

                'SYSTEM'

            )

        ),


    content TEXT NOT NULL,


    sequence_number INTEGER NOT NULL,


    retrieval_query TEXT,


    citations JSONB,


    generation_metadata JSONB,


    status VARCHAR(20) NOT NULL

        CHECK (

            status IN (

                'PENDING',

                'COMPLETED',

                'FAILED'

            )

        ),


    error_message TEXT,


    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),


    deleted_at TIMESTAMPTZ,


    CONSTRAINT uq_message_sequence

        UNIQUE (conversation_id, sequence_number)

);


-- ============================================================================

-- INDEXES

-- ============================================================================


CREATE INDEX idx_users_status

    ON users(status);


CREATE INDEX idx_documents_owner

    ON documents(owner_id);


CREATE INDEX idx_documents_status

    ON documents(status);


CREATE INDEX idx_documents_checksum

    ON documents(file_checksum);


CREATE INDEX idx_documents_created_at

    ON documents(created_at DESC);


CREATE INDEX idx_document_chunks_document

    ON document_chunks(document_id);


CREATE INDEX idx_processing_jobs_document

    ON processing_jobs(document_id);


CREATE INDEX idx_processing_jobs_status

    ON processing_jobs(status);


CREATE INDEX idx_conversations_user

    ON conversations(user_id);


CREATE INDEX idx_messages_conversation

    ON messages(conversation_id);


CREATE INDEX idx_messages_parent

    ON messages(parent_message_id);


-- JSONB GIN indexes

CREATE INDEX idx_documents_okf_metadata

    ON documents

    USING GIN (okf_metadata);


CREATE INDEX idx_documents_parsed_json

    ON documents

    USING GIN (parsed_json);


CREATE INDEX idx_conversations_scope

    ON conversations

    USING GIN (scope_json);


-- pgvector similarity search index

-- Recommended after data load


CREATE INDEX idx_document_chunks_embedding

ON document_chunks

USING ivfflat (embedding vector_cosine_ops)

WITH (lists = 100);