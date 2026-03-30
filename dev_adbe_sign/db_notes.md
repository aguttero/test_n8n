## SQLite
# User DB
    id INTEGER PRIMARY KEY,
    email varchar (250) NOT NULL UNIQUE, // FK
    user_id varchar (250) NOT NULL UNIQUE, // FK
    company varchar (250)

# Group DB
    id INTEGER PRIMARY KEY,
    groupid varchar (250) NOT NULL UNIQUE,
    groupname varchar (250)

# Agreement DB   

## SQL Alchemy