import pandas as pd

from sqlalchemy import insert, select, update
from sqlalchemy.sql.expression import cast
from sqlalchemy.types import TIMESTAMP, DATE, TIME, INTEGER, FLOAT
from sqlalchemy_utils.functions import drop_database, database_exists, create_database
from src.db.utils import connect, delete_all, reset_counter, execute_script


def lookup_status_code(status):
    """Status code mapping from the numeric representation to the meaning"""
    lookup = {-1: "Very Bad", 0: "Bad", 1: "Not Checked", 2: "Checked", 3: "Validated"}
    return lookup[status]


class Client:
    def __init__(self, uri: str, config: dict):
        self.uri = uri
        self.config = config

    def create_database(self):
        """Create the database from scratch"""
        if database_exists(self.uri):
            drop_database(self.uri)
        create_database(self.uri)

        self.metadata_obj, self.engine = connect(self.uri)
        execute_script("./sql/create_tables.sql", self.engine)
        # refresh engine to get table metadata
        self.metadata_obj, self.engine = connect(self.uri)

    def delete_all(self, name: str):
        """Delete all records in the database"""
        delete_all(name, self.metadata_obj, self.engine)

    def reset_counter(self, table_name: str, id_name: str):
        """Reset index counters in the database"""
        reset_counter(table_name, id_name, self.engine)

    def create_cpf_summary(self, cpf_metadata: pd.DataFrame):
        """Create the CPF summary table"""
        cpf_metadata.to_sql("cpf_summary", self.engine, if_exists="replace")

    def create_scenarios(self, shot_metadata: pd.DataFrame):
        """Create the scenarios metadata table"""
        ids = shot_metadata["scenario_id"].unique()
        scenarios = shot_metadata["scenario"].unique()

        data = pd.DataFrame(dict(id=ids, name=scenarios)).set_index("id")
        data = data.dropna()
        data.to_sql("scenarios", self.engine, if_exists="append")

    def create_shots(self, shot_metadata: pd.DataFrame):
        """Create the shot metadata table"""
        shot_metadata["facility"] = "MAST"
        shot_metadata = shot_metadata.set_index("shot_id")
        shot_metadata["scenario"] = shot_metadata["scenario_id"]
        shot_metadata = shot_metadata.drop(["scenario_id", "reference_id"], axis=1)
        shot_metadata.to_sql("shots", self.engine, if_exists="append")

    def create_signals(self, signal_metadata: pd.DataFrame):
        """Create the signal metadata table"""
        signal_metadata["name"] = signal_metadata["signal_name"]
        signal_metadata["description"] = signal_metadata["description"]
        signal_metadata["signal_type"] = signal_metadata["type"]
        signal_metadata["quality"] = signal_metadata["signal_status"].map(
            lookup_status_code
        )
        signal_metadata["dimensions"] = signal_metadata["dimensions"].map(list)
        signal_metadata["doi"] = ""

        signal_metadata = signal_metadata.drop(
            [
                "shot_nums",
                "shape",
                "time_index",
                "label",
                "generic_name",
                "pass_",
                "source_alias",
                "signal_status",
                "mds_name",
                "type",
                "shot",
                "signal_name",
            ],
            axis=1,
        )

        signal_metadata.to_sql("signals", self.engine, if_exists="append", index=False)

    def create_shot_signal_links(self, sample_metadata: pd.DataFrame):
        signals_table = self.metadata_obj.tables["signals"]
        stmt = select(signals_table.c.signal_id, signals_table.c.name)
        signals = pd.read_sql(stmt, con=self.engine.connect())
        sample_metadata = pd.merge(
            sample_metadata, signals, left_on="name", right_on="name"
        )
        sample_metadata["quality"] = sample_metadata["signal_status"].map(
            lookup_status_code
        )
        sample_metadata["shape"] = sample_metadata["shape"].map(lambda x: x.tolist())

        columns = ["signal_id", "shot_nums", "quality", "shape"]
        sample_metadata = sample_metadata[columns]
        sample_metadata = sample_metadata.rename(dict(shot_nums="shot_id"), axis=1)

        sample_metadata = sample_metadata.set_index("shot_id")
        sample_metadata.to_sql("shot_signal_link", self.engine, if_exists="append")

    def create_sources(self, source_metadata: pd.DataFrame):
        source_metadata = source_metadata
        source_metadata["name"] = source_metadata["source_alias"]
        source_metadata["source_type"] = source_metadata["type"]
        source_metadata = source_metadata[["description", "name", "source_type"]]
        source_metadata = source_metadata.drop_duplicates()
        source_metadata = source_metadata.sort_values("name")
        source_metadata.to_sql("sources", self.engine, if_exists="append", index=False)

    def create_shot_source_links(self, sources_metadata: pd.DataFrame):
        sources_metadata = sources_metadata
        sources_metadata["source"] = sources_metadata["source_alias"]
        sources_metadata["quality"] = sources_metadata["status"].map(lookup_status_code)
        sources_metadata["shot_id"] = sources_metadata["shot"].astype(int)
        sources_metadata = sources_metadata[
            ["source", "shot_id", "quality", "pass", "format"]
        ]
        sources_metadata = sources_metadata.sort_values("source")
        sources_metadata.to_sql(
            "shot_source_link", self.engine, if_exists="append", index=False
        )
