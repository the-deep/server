# Install remote2_syslog for logging
curl -L -o /tmp/syslog2 "https://github.com/papertrail/remote_syslog2/releases/download/v0.19/remote-syslog2_0.19_amd64.deb"
dpkg -i /tmp/syslog2
rm /tmp/syslog2

# Download remote2_syslog init
curl -L -o /etc/init/remote_syslog.conf "https://raw.githubusercontent.com/papertrail/remote_syslog2/master/examples/remote_syslog.upstart.conf"
curl -L -o /etc/init.d/remote_syslog "https://raw.githubusercontent.com/papertrail/remote_syslog2/master/examples/remote_syslog.init.d"
chmod +x /etc/init.d/remote_syslog
update-rc.d remote_syslog defaults

mkdir /var/log/uwsgi

# Add Cloud Watch metrics [Note: requires unzip, libwww-perl, libdatetime-perl]
mkdir -p /aws-script

curl -o /tmp/cloudWatchMonitoringScripts.zip http://aws-cloudwatch.s3.amazonaws.com/downloads/CloudWatchMonitoringScripts-1.2.1.zip
unzip /tmp/cloudWatchMonitoringScripts.zip -d /aws-script

touch /var/log/cron.log
