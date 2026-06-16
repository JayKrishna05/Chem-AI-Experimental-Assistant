CREATE TABLE reactions (
    reaction_id VARCHAR NOT NULL,
    reaction_type VARCHAR,
    source_dataset VARCHAR,
    source_dataset_id VARCHAR,
    reactants_json JSON,
    reagents_json JSON,
    catalysts_json JSON,
    products_json JSON,
    conditions_json JSON
);

CREATE TABLE procedures (
    reaction_id VARCHAR NOT NULL,
    reaction_type VARCHAR,
    temperature_c DOUBLE,
    yield_percent DOUBLE,
    procedure_text VARCHAR
);

CREATE TABLE molecules (
    smiles VARCHAR NOT NULL,
    occurrences BIGINT
);

CREATE TABLE ingestion_audit (
    dataset VARCHAR NOT NULL,
    source_path VARCHAR NOT NULL,
    expected_count BIGINT NOT NULL,
    imported_count BIGINT NOT NULL,
    ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
