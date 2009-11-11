SELECT 
	procpid,
	now() - query_start AS has_been_running_for,
	-- query_start,
	datname AS database_name, 
	usename AS "user",
	current_query
	FROM
		pg_stat_activity 
	WHERE 
		current_query NOT LIKE '<IDLE>%' 
	ORDER BY has_been_running_for DESC;
