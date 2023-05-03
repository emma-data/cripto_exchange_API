class User:
    def __init__(self, user_id, balance=0):
        self.id = user_id
        self.balance = balance

    
    @classmethod
    # Crear usuario
    def create(cls, conn, user_id):
        c = conn.cursor()
        c.execute("INSERT INTO users (id) VALUES (?)", (user_id,))
        conn.commit()
        return cls(user_id)

    
    @classmethod
    # Devuelve la instancia y su balance actualizado
    def usuario(cls, conn, user_id):
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE id=?", (user_id,))
        resultado = c.fetchone()
        if resultado is None:
            return None
        return cls(user_id, balance=resultado[0])

    
    def depositar(self, conn, monto):
        #Depositar y actualizar balance
        nuevo_balance = self.balance + monto
        c = conn.cursor()
        c.execute("UPDATE users SET balance=? WHERE id=?", (nuevo_balance, self.id))
        conn.commit()
        self.balance = round(nuevo_balance, 2)


    def posiciones(self, conn):
        # Listar activos tradeados por el usuario
        c = conn.cursor()
        c.execute("SELECT DISTINCT asset FROM transactions WHERE user_id = ?", (self.id,))
        assets = [row[0] for row in c.fetchall()]

        # Calcular posición actual y precio promedio or activo
        positions = []
        for asset in assets:
            c.execute("SELECT SUM(quantity), AVG(price) FROM transactions WHERE user_id = ? AND asset = ?",
                      (self.id, asset))
            result = c.fetchone()
            position = {'asset': asset, 'quantity': result[0], 'avg_price': result[1], 'total':result[0]*result[1]}
            positions.append(position)
        print("Positions: ", positions)
        return positions


    def pnl(self, conn):
        #Obtener posiciones y balance actual
        positions = self.posiciones(conn)
        current_balance = self.balance

        c = conn.cursor()
        c.execute("SELECT asset, quantity, price, type FROM transactions WHERE user_id = ?", (self.id,))
        rows = c.fetchall()
        pnl = 0.0
        for row in rows:
            asset, quantity, price, type_ = row
            if type_.upper() == "BUY":
                pnl -= quantity * price
            elif type_.upper() == "SELL":
                pnl -= quantity * price
        open_positions = 0
        for position in positions:
            open_positions += position['quantity'] * position['avg_price']
        pnl += open_positions
        #Falta implementar el P&L no realizado para las posiciones abiertas
        return {"pnl": pnl}