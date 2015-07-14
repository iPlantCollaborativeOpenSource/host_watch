Host watch monitor
==================
Monitor the host system, generate logs and forward to logstash.

# Requirements:
- python-logstash
- supervisor
- shapeshift

# Setup
Install `supervisord` then follow the steps below.

```bash
cp extras/logrotate.host_watch /etc/logrotate.d
cp extras/host_watch.conf /etc/supervisor/conf.d
supervisorctl reread
supervisorctl update
```

# LICENSE
See the LICENSE file.
