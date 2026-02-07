    def place_grid(self):
        price = self.get_price()
        
        # Calcular ATR Dinâmico
        atr = self.calculate_atr()
        
        if atr:
            # Calcular espaçamento dinâmico
            dynamic_spacing = (atr / price) * self.atr_multiplier
            # Garantir mínimo
            self.grid_spacing = max(dynamic_spacing, self.min_spacing)
            print(f" Preço: ${price:.2f} | ATR: {atr:.2f} | Spacing Dinâmico: {self.grid_spacing*100:.2f}%")
        else:
            print(f" Preço: ${price:.2f} | ATR Falhou -> Usando Fixo: 0.15%")
            self.grid_spacing = 0.0015