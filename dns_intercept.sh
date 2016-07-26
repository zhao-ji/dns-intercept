#!/bin/sh

### BEGIN INIT INFO
# Provides:          dns_intercept
# Required-Start:    $remote_fs
# Required-Stop:     $remote_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start or stop or restart the DNS intercept
### END INIT INFO


set -e

NAME=dns_intercept
PIDFILE=/var/run/$NAME.pid

DAEMON=/home/nightwish/nipple/intercept_dns/dns_server.py
DAEMON_OPTS="--logfile /home/nightwish/nipple/intercept_dns/log_dns_history --intercept /home/nightwish/nipple/intercept_dns/zonefile --upstream 172.16.0.1 --host 0.0.0.0 --port 53"

case "$1" in 
    start)
        echo -n "Starting daemon: "$NAME
        start-stop-daemon --start --background --make-pidfile --pidfile $PIDFILE --exec $DAEMON -- $DAEMON_OPTS
        echo "."
        ;;
    stop)
        echo -n "Stopping daemon: "$NAME
        start-stop-daemon --stop --quiet --oknodo --pidfile $PIDFILE
        echo "."
        ;;
    restart)
        echo -n "Restarting daemon: "$NAME
        start-stop-daemon --stop --quiet --oknodo --retry 30 --pidfile $PIDFILE
        start-stop-daemon --start --background --make-pidfile --pidfile $PIDFILE --exec $DAEMON -- $DAEMON_OPTS
        echo "."
        ;;
    *)
        echo "Usage: "$1" {start|stop|restart}"
        exit 1
esac

exit 0
