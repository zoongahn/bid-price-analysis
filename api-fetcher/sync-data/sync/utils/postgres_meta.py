class PostgresMeta:
	def __init__(self, conn, schema: str = "public"):
		self.conn = conn
		self.cur = conn.cursor()
		self.schema = schema

	def get_column_types(self, table_name: str) -> dict[str, str]:
		"""
		{컬럼명: data_type} 딕셔너리 반환 (GENERATED 컬럼 제외)
		"""
		self.cur.execute(
			"""
			SELECT column_name, data_type, is_generated
			FROM   information_schema.columns
			WHERE  table_name = %s
			  AND  table_schema = %s
			ORDER  BY ordinal_position;
			""",
			(table_name, self.schema),
		)
		return {
			row[0]: row[1]
			for row in self.cur.fetchall()
			if row[2] != 'ALWAYS'  # GENERATED 컬럼 제외
		}

	def get_column_info(self, table_name: str):
		self.cur.execute(
			"""SELECT
				a.attname                                        AS column_name,
				pgd.description                                  AS comment,
				pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
				CASE WHEN a.attnotnull THEN 'NO' ELSE 'YES' END AS is_nullable
			FROM pg_catalog.pg_attribute a
			JOIN pg_catalog.pg_class     c ON a.attrelid   = c.oid
			JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
			LEFT JOIN pg_catalog.pg_description pgd
				   ON pgd.objoid = a.attrelid AND pgd.objsubid = a.attnum
			WHERE c.relname   = %s
			  AND n.nspname   = %s
			  AND a.attnum   > 0
			  AND NOT a.attisdropped
			ORDER BY a.attnum;
			""", (table_name, self.schema),
		)
		return self.cur.fetchall()
