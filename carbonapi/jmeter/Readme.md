Variable             Default value
http_addr            127.0.0.1
http_port            8889
urls                 test.csv (CSV file with reader. At this time with one field - target)
duration             300 (Test duration in s)
rump-up              0 (Test ramp-up period in s)
delay                100 (Delay bettween requests in ms)
env                  staging (environment on metric)
graphite_relay       127.0.0.1
metric_prefix        DevOps.loadTesting.jmeter (Prefix for metric: "${metrix_prefix}.${env}.carbonapi.")
http_users_1_hour    10
http_users_1_day     2
http_users_1_week    2
http_users_3_month   1


Run in cli mode
    mkdir report
    jmeter.sh -Jhttp_addr=test-graphite-s1 -Jhttp_users_1_hour=0 -Jgraphite_relay=graphite-relay -n -t carbonapi.jmx -l report/results.csv

For generate html report
    mkdir -p report/jmeter
    jmeter.sh  -g results.csv -o report/jmeter
