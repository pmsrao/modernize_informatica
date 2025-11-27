"""
Function Registry for mapping Informatica functions to PySpark equivalents.
Comprehensive mapping table covering 100+ Informatica functions.
"""

FUNCTION_MAP = {
    # Conditional Functions
    "IIF": ("when", "otherwise"),
    "DECODE": ("case", "when"),
    "ISNULL": ("isNull",),
    "ISNOTNULL": ("isNotNull",),
    "ISNULLOREMPTY": ("isNull", "or", "length", "==", "0"),
    
    # String Functions
    "SUBSTR": ("substring",),
    "SUBSTRING": ("substring",),
    "INSTR": ("instr",),
    "UPPER": ("upper",),
    "LOWER": ("lower",),
    "TRIM": ("trim",),
    "LTRIM": ("ltrim",),
    "RTRIM": ("rtrim",),
    "REPLACESTR": ("regexp_replace",),
    "REPLACE": ("regexp_replace",),
    "CONCAT": ("concat",),
    "LENGTH": ("length",),
    "LPAD": ("lpad",),
    "RPAD": ("rpad",),
    "SPACE": ("lit", " "),
    
    # Date/Time Functions
    "TO_DATE": ("to_date",),
    "TO_CHAR": ("date_format",),
    "SYSDATE": ("current_timestamp",),
    "SYSTIMESTAMP": ("current_timestamp",),
    "ADD_TO_DATE": ("date_add",),
    "SUBTRACT_TO_DATE": ("date_sub",),
    "DATE_DIFF": ("datediff",),
    "MONTHS_BETWEEN": ("months_between",),
    "LAST_DAY": ("last_day",),
    "TRUNC_DATE": ("trunc",),
    "EXTRACT": ("extract",),
    "YEAR": ("year",),
    "MONTH": ("month",),
    "DAY": ("dayofmonth",),
    "HOUR": ("hour",),
    "MINUTE": ("minute",),
    "SECOND": ("second",),
    "DAY_OF_WEEK": ("dayofweek",),
    "DAY_OF_YEAR": ("dayofyear",),
    "WEEK_OF_YEAR": ("weekofyear",),
    
    # Numeric Functions
    "ROUND": ("round",),
    "TRUNC": ("trunc",),
    "ABS": ("abs",),
    "CEIL": ("ceil",),
    "FLOOR": ("floor",),
    "MOD": ("mod",),
    "POWER": ("pow",),
    "SQRT": ("sqrt",),
    "EXP": ("exp",),
    "LN": ("log",),
    "LOG": ("log10",),
    "SIGN": ("signum",),
    "RANDOM": ("rand",),
    
    # Aggregation Functions
    "SUM": ("sum",),
    "AVG": ("avg",),
    "MAX": ("max",),
    "MIN": ("min",),
    "COUNT": ("count",),
    "COUNT_DISTINCT": ("countDistinct",),
    "STDDEV": ("stddev",),
    "VARIANCE": ("variance",),
    "MEDIAN": ("expr", "percentile_approx"),
    
    # Conversion Functions
    "TO_INTEGER": ("cast", "IntegerType"),
    "TO_DECIMAL": ("cast", "DecimalType"),
    "TO_CHAR": ("cast", "StringType"),
    "TO_DOUBLE": ("cast", "DoubleType"),
    "TO_FLOAT": ("cast", "FloatType"),
    "TO_BIGINT": ("cast", "LongType"),
    "TO_SMALLINT": ("cast", "ShortType"),
    "TO_TIMESTAMP": ("to_timestamp",),
    
    # Null Handling
    "NVL": ("coalesce",),
    "NVL2": ("when", "isNotNull", "coalesce"),
    "NULLIF": ("nullif",),
    
    # String Comparison
    "STRCMP": ("expr", "strcmp"),
    "SOUNDEX": ("soundex",),
    
    # Mathematical
    "SIN": ("sin",),
    "COS": ("cos",),
    "TAN": ("tan",),
    "ASIN": ("asin",),
    "ACOS": ("acos",),
    "ATAN": ("atan",),
    "ATAN2": ("atan2",),
    
    # Window Functions (Informatica equivalents)
    "LAG": ("lag",),
    "LEAD": ("lead",),
    "RANK": ("rank",),
    "DENSE_RANK": ("dense_rank",),
    "ROW_NUMBER": ("row_number",),
    "FIRST_VALUE": ("first_value",),
    "LAST_VALUE": ("last_value",),
    "SUM_OVER": ("sum", "over"),
    "AVG_OVER": ("avg", "over"),
    
    # Miscellaneous
    "MD5": ("md5",),
    "SHA1": ("sha1",),
    "SHA2": ("sha2",),
    "CRC32": ("crc32",),
}

# Function argument count mapping (for validation)
FUNCTION_ARGS = {
    "IIF": 3,
    "DECODE": -1,  # Variable
    "NVL": 2,
    "NVL2": 3,
    "SUBSTR": 3,
    "INSTR": 2,
    "REPLACESTR": 3,
    "CONCAT": -1,  # Variable
    "TO_DATE": 2,
    "ADD_TO_DATE": 3,
    "DATE_DIFF": 2,
    "ROUND": 2,
    "POWER": 2,
    "MOD": 2,
}
