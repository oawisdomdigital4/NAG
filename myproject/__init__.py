# Optional: allow using PyMySQL as a drop-in replacement for MySQLdb
try:
	import pymysql
	pymysql.install_as_MySQLdb()
except Exception:
	# If PyMySQL is not installed, fall back to mysqlclient (MySQLdb)
	pass

