Host watch monitor
==================
Monitor the host system, generate logs and forward to logstash.

# Requirements:
- python-logstash
- supervisor
- shapeshift

# Setup
Install `supervisord` then follow the steps below.

Edit the host_watch.conf.dist file to set the correct directories

```bash
cp extras/logrotate.host_watch /etc/logrotate.d
cp extras/host_watch.conf.dist /etc/supervisor/conf.d/host_watch.conf
supervisorctl reread
supervisorctl update
```

# LICENSE
See the LICENSE file.
