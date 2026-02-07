#!/usr/bin/env python3
"""
 FEEDBACK DEPARTMENT (Central de Erros e Inteligência de Falhas)
Objetivo: Registrar, persistir e analisar erros reportados por todos os agentes.
O Orchestrator consulta este departamento antes de agir para evitar "ir para a guerra" com ferramentas quebradas.
"""

import json
import time
import os
from typing import Dict, Any, List

class FeedbackDepartment:
    def __init__(self, storage_file="system_health.json"):
        self.storage_file = storage_file
        self._load_data()

    def _load_data(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                self.data = {"incidents": [], "status": "OPERATIONAL"}
        else:
            self.data = {"incidents": [], "status": "OPERATIONAL"}

    def _save_data(self):
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"️ Erro ao salvar Feedback DB: {e}")

    def report_incident(self, component: str, error_code: str, message: str, severity: str = "WARNING"):
        """
        Reporta um novo incidente/erro.
        Severity: INFO, WARNING, CRITICAL, BLOCKER
        """
        incident = {
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "component": component,
            "error_code": str(error_code),
            "message": str(message),
            "severity": severity,
            "resolved": False
        }
        
        # Adicionar ao log
        self.data["incidents"].append(incident)
        
        # Manter apenas os últimos 50 incidentes
        if len(self.data["incidents"]) > 50:
            self.data["incidents"] = self.data["incidents"][-50:]
            
        # Atualizar Status Global se for Crítico
        if severity in ["CRITICAL", "BLOCKER"]:
            self.data["status"] = "DEGRADED"
            
        self._save_data()
        print(f" [FEEDBACK] Novo Incidente Registrado: {component} - {message}")

    def consult_intelligence(self, component: str = None) -> Dict[str, Any]:
        """
        Consulta a inteligência de falhas.
        Se component for fornecido, retorna riscos específicos para aquele componente.
        """
        self._load_data() # Recarregar para ter dados frescos
        
        recent_incidents = [
            i for i in self.data["incidents"] 
            if not i["resolved"] and (time.time() - i["timestamp"] < 3600) # Última hora
        ]
        
        if component:
            component_incidents = [i for i in recent_incidents if i["component"] == component]
            risk_level = "LOW"
            if any(i["severity"] == "CRITICAL" for i in component_incidents):
                risk_level = "HIGH"
            elif component_incidents:
                risk_level = "MEDIUM"
                
            return {
                "risk_level": risk_level,
                "active_warnings": len(component_incidents),
                "recent_errors": [i["message"] for i in component_incidents[-3:]]
            }
            
        return {
            "system_status": self.data["status"],
            "total_active_incidents": len(recent_incidents)
        }

    def clear_incidents(self, component: str = None):
        """Limpa incidentes (marca como resolvido)"""
        for i in self.data["incidents"]:
            if component is None or i["component"] == component:
                i["resolved"] = True
        
        if component is None:
            self.data["status"] = "OPERATIONAL"
            
        self._save_data()

if __name__ == "__main__":
    # Teste Rápido
    fb = FeedbackDepartment()
    fb.report_incident("BackpackAPI", "500", "Internal Server Error", "CRITICAL")
    print(fb.consult_intelligence("BackpackAPI"))
