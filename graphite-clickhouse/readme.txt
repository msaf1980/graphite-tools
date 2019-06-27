Variable             Default value
http_addr            127.0.0.1
http_port            9090
test_urls            test.urls
http_users_3_hours   5
http_users_1_day     2	
http_users_1_week    2
http_users_3_month   1

Run in cli mode
    jmeter.sh -n -Jhttp_addr=localhost -t graphite-clickhouse.jmx -l test.urls

