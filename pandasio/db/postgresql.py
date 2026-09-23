import io

from psycopg2.extras import execute_values

from .base import BaseDataFrameDatabaseSaver
from .utils import get_unique_field_names, get_upsert_clause_sql


class DataFrameDatabaseSaver(BaseDataFrameDatabaseSaver):

    def save(self, dataframe, model, returning_columns=None):
        if dataframe.empty:
            return [] if returning_columns else None
        buffer = io.StringIO()
        dataframe.to_csv(buffer, index=False, header=False, na_rep='\\N')
        buffer.seek(0)
        copy_query = """
            COPY %(table)s (%(columns)s) FROM stdin CSV NULL '\\N';
        """ % {'table': model._meta.db_table, 'columns': ','.join(dataframe.columns)}
        try:
            with self._connection.cursor() as cursor:
                cursor.copy_expert(sql=copy_query, file=buffer)
            self._connection.commit()
            return [] if returning_columns else None
        except Exception as e:
            self._connection.rollback()
            print(f"PandasIO saving error: {e}")
            buffer.close()
            return self.upsert(dataframe=dataframe, model=model, returning_columns=returning_columns)
        finally:
            if not buffer.closed:
                buffer.close()

    def upsert(self, dataframe, model, returning_columns=None):
        if dataframe.empty:
            return [] if returning_columns else None

        columns = list(dataframe.columns)
        unique_columns = get_unique_field_names(model)
        upsert_clause = get_upsert_clause_sql(model, columns=columns)

        conflict_statement = (
            """
            ON CONFLICT (%(unique_columns)s)
            %(do_statement)s
        """
            % {
                "unique_columns": ", ".join(unique_columns),
                "do_statement": "DO UPDATE SET %s " % upsert_clause
                if upsert_clause
                else "DO NOTHING ",
            }
            if unique_columns
            else ""
        )

        returning_statement = (
            ("RETURNING %s" % ", ".join(returning_columns)) if returning_columns else ""
        )

        query = (
            """
            INSERT INTO %(table)s (%(columns)s)
            VALUES %%s
        """
            % {
                "table": model._meta.db_table,
                "columns": ",".join(columns),
            }
            + conflict_statement
            + returning_statement
        )

        rows = dataframe.itertuples(index=False, name=None)

        with self._connection.cursor() as cursor:
            try:
                returning = execute_values(
                    cursor,
                    query,
                    rows,
                    page_size=10000,
                    fetch=bool(returning_columns),
                )
                self._connection.commit()
                if returning_columns:
                    return returning
            except Exception as e:
                print(e)
                self._connection.rollback()
                raise e
