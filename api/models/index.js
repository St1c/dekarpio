const mysql = require('promise-mysql');

const pool = mysql.createPool({
    host: process.env.DB_HOST || 'database',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || 'root',
    database: process.env.DB_DATABASE || 'dekarpio',
    multipleStatements: true,
    connectionLimit: 130,
    waitForConnections: true,
    debug: false
});

if (process.env.APP_ENV === 'development') {
    pool.on('connection', connection => {
        // console.log('Connection %d opened', connection.threadId);
        connection.on('enqueue', sequence => {
            if ('Query' === sequence.constructor.name) {
                console.log(Date.now() + ' ' + sequence.sql);
            }
        });
    });

    pool.on('acquire', function (connection) {
        // console.log('Connection %d acquired', connection.threadId);
    });

    pool.on('release', connection => {
        // console.log('Connection %d released', connection.threadId);
    });
}

var database = {
    pool: pool,

    init(tableName, readableAttributes = ['id'], writableAttributes = ['id']) {
        this.tableName = tableName;
        this.readableAttributes = readableAttributes;
        this.writableAttributes = writableAttributes;
    },

    async connect() {
        this.connection = await this.pool.getConnection();

        return this.connection;
    },

    async get(needle = undefined) {
        let query;
        if (needle && typeof needle == 'object') {
            query = this._prepareSelectQuery(needle)
            console.log(query)
        } else {
            query = mysql.format(
                'SELECT ?? FROM ??', [this.readableAttributes, this.tableName]
            );
        }

        return this.query(query);
    },

    /**
     * Find in DB table by property:value pairs
     * 
     * @param {property: value} obj property:value pair for finding in Table
     * @param {number} limit Required number of rows returned
     */
    async find(obj, limit = 0) {
        if (!obj || !Object.values(obj)[0]) {
            throw new Error('Missing parameters for find query');
        }

        return await this.query(this._prepareSelectQuery(obj, limit));
    },

    /**
     * Find or create new record in DB
     * No need to try/catch, default error handler will catch thrown error
     * 
     * @param {property: value} obj Property: Table columns name, value: search value
     */
    async findOrCreate(obj) {
        var rows = await this.find(obj);
        var id = rows[0] ? rows[0].id : null;
        if (!id) {
            rows = await this.create(obj);
            id = rows.insertId;
        };

        return id;
    },

    /**
     * Create new DB row with given column:value pairs
     * 
     * @param {Object} obj column:value pairs in JS Object
     */
    create(obj) {
        return this.query(mysql.format(
            'INSERT INTO ?? SET ??',
            [this.tableName, obj]
        ));
    },

    /**
     * Delete sected row from DB
     * 
     * @param {number} id Row id to delete
     */
    delete(id) {
        return this.query(mysql.format(
            'DELETE FROM ?? WHERE `id` = ?', [this.tableName, id]
        ));
    },

    /**
     * Shadow implementation of native mysql 
     * query to ensure connection is defined
     */
    query(query, params) {
        if (!this.connection) {
            throw new Error('Missing DB connection. Please create connection with db.connect() first!');
        }

        return this.connection.query(query, params);
    },

    /**
     * Checks if all keys in input object are valid column names in table schema
     * 
     * @param {Object} input object which should be written to DB
     */
    checkIfWritableAttributeExists(input) {
        Object.keys(input).map(key => {
            if (!this.writableAttributes.includes(key)) {
                throw new Error(`Column '${key}' does not exist in '${this.tableName}' schema`);
            }
        });
    },

    // Private methods

    /**
     * Prepare sql query based on column name and value
     * 
     * @param {Object} obj Column:value pairs
     */
    _prepareSelectQuery(obj, limit = 0) {
        const keys = Object.keys(obj);
        const values = Object.values(obj);

        const queryString = this._prepareSelectQueryString(keys.length, limit);
        const keyValuePairs = this._transformObjectToSearchArray(keys, values);

        return mysql
            .format(queryString, [this.readableAttributes, this.tableName, ...keyValuePairs])
            .replace('= NULL', 'IS NULL');
    },

    /**
     * Prepare raw SQL query template optimized for better using of indices
     * 
     * @param {number} pairsNumber number of column:value pairs
     * @param {number} limit limit number of results
     */
    _prepareSelectQueryString(pairsNumber, limit) {
        if (pairsNumber < 1) return;

        let query;
        if (pairsNumber == 1) {
            query = 'SELECT ?? FROM ?? WHERE ?? = ?';
        } else {
            query = 'SELECT ?? FROM ?? WHERE ?? = ?' + ' AND ?? = ?'.repeat(pairsNumber - 1);
        }

        if (limit > 0) {
            query += ' LIMIT ' + limit;
        }

        return query
    },

    /**
     * Tranform keys and values obtained from search 
     * object into array usable in mysql.prepare function
     * (e.g. {column1: value1, column2: value2} becomes [ column1, value1, column2, value2 ])
     * 
     * @param {Array} keys Keys array
     * @param {Array} values Values array
     * 
     * @returns {Array} [ key1, value1, key2, value2 ...]
     */
    _transformObjectToSearchArray(keys, values) {
        return keys.reduce((combArr, elem, i) => combArr.concat(elem, values[i]), []);
    }
}

module.exports = database;