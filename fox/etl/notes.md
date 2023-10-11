# ETL

## Development Ideas

Goals:
- ETL pipeline, providing junction between Django and Pandas
- Using Celery? => this simplifies task pipeline setup

Technical principles:
- keep it simple, keep concerns separated
- work as much as possible with dataframe

### Extract
- Source Providers:
    - HTTP(S): raw text, json, file (saving)
    - FTP, SFTP, FILE
- Scanner
- Extract data from: json, html, xml, regex

### Transform


### Load
Django-Pandas tools:
- Pandas: dataframe accessors
- Django: queryset to handle dataframe

Registry:
- Registry of Record (which can be models):
    - Handle multiple type of records or model inside RecordSet
- RecordSet:
    - is the datastore (df + record/model class)
    - shortcut function  (save, update, etc.)
- Relation:
    - types: One->Many, Many->Many
    - dependency graph
