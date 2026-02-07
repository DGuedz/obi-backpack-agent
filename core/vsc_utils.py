
class VSCParser:
    """
     VSC (Value-Separated Content) PARSER STRICT
    Regras:
    1. Uma entidade por linha.
    2. Valores separados por vírgula.
    3. Ordem = Significado (Schema Externo).
    4. Sem metadados implícitos.
    5. Falha se inválido (Sem 'autofill').
    """
    
    @staticmethod
    def parse_line(line, expected_types=None):
        """
        Lê uma linha VSC e valida os tipos se fornecido um schema.
        :param line: String bruta (ex: "Laptop,3999.90")
        :param expected_types: Lista de tipos esperados (ex: [str, float])
        :return: Lista de valores tipados ou lança Exceção.
        """
        if not line or line.strip() == "":
            return None
            
        parts = [p.strip() for p in line.split(',')]
        
        if expected_types:
            if len(parts) != len(expected_types):
                raise ValueError(f"VSC Error: Esperado {len(expected_types)} campos, recebido {len(parts)}. Linha: {line}")
            
            typed_parts = []
            for i, (val, type_cls) in enumerate(zip(parts, expected_types)):
                try:
                    if type_cls == bool:
                        # Tratamento especial para bool
                        clean_val = val.lower()
                        if clean_val == 'true': typed_parts.append(True)
                        elif clean_val == 'false': typed_parts.append(False)
                        else: raise ValueError
                    else:
                        typed_parts.append(type_cls(val))
                except:
                    raise TypeError(f"VSC Error: Campo {i} ('{val}') inválido. Esperado {type_cls.__name__}.")
            return typed_parts
            
        return parts

    @staticmethod
    def read_file(file_path, schema=None):
        """
        Lê arquivo VSC inteiro.
        :param schema: Lista de Listas de tipos (uma lista por linha esperada)
                       OU Lista única se todas as linhas seguirem o mesmo padrão (ex: products).
        """
        results = []
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        # Remove empty lines
        lines = [l.strip() for l in lines if l.strip()]
        
        for i, line in enumerate(lines):
            # Se schema for lista de listas, usa o schema da linha correspondente
            current_schema = None
            if schema:
                if isinstance(schema[0], list):
                    if i < len(schema):
                        current_schema = schema[i]
                else:
                    current_schema = schema # Schema repetitivo
            
            parsed = VSCParser.parse_line(line, current_schema)
            if parsed:
                results.append(parsed)
                
        return results
