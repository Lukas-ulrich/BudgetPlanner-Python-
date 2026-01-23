# ============================================
# calculations.py - Berechnungslogik
# ============================================
import numpy as np
from typing import List, Dict, Tuple


class BudgetCalculator:
    """Berechnungen für Budget-Analysen"""
    
    @staticmethod
    def calculate_totals(month_data: MonthData, structure: dict) -> Dict[str, float]:
        """Berechnet Gesamtsummen"""
        totals = {
            'income': 0.0,
            'expenses': 0.0,
            'fixed': 0.0,
            'variable': 0.0,
            'balance': 0.0
        }
        
        category_totals = {}
        
        for (category, subcat, item), trans in month_data.get_all_transactions().items():
            amount = trans.amount
            
            # Kategorisierung
            if "Einnahmen" in category or category.lower().startswith("ein"):
                totals['income'] += amount
            elif "Fix" in category or category.lower().startswith("fix"):
                totals['fixed'] += amount
                totals['expenses'] += amount
            elif "Variable" in category or category.lower().startswith("var"):
                totals['variable'] += amount
                totals['expenses'] += amount
            elif category == "Sparen":
                totals['expenses'] += amount
                totals['variable'] += amount
            else:
                totals['expenses'] += amount
                totals['variable'] += amount
            
            # Category totals
            if category not in category_totals:
                category_totals[category] = 0.0
            category_totals[category] += amount
        
        totals['balance'] = totals['income'] - totals['expenses']
        totals['categories'] = category_totals
        
        return totals
    
    @staticmethod
    def calculate_savings_rate(income: float, expenses: float) -> float:
        """Berechnet Sparquote in Prozent"""
        if income == 0:
            return 0.0
        return ((income - expenses) / income) * 100.0
    
    @staticmethod
    def get_top_expenses(month_data: MonthData, n: int = 3) -> List[Tuple[str, float]]:
        """Gibt Top-N Ausgaben zurück"""
        subcategory_totals = {}
        
        for (category, subcat, item), trans in month_data.get_all_transactions().items():
            if "Einnahmen" not in category:
                key = f"{category} / {subcat}"
                if key not in subcategory_totals:
                    subcategory_totals[key] = 0.0
                subcategory_totals[key] += trans.amount
        
        sorted_expenses = sorted(subcategory_totals.items(), key=lambda x: x[1], reverse=True)
        return sorted_expenses[:n]
    
    @staticmethod
    def calculate_year_statistics(months_data: List[Tuple[str, MonthData]], structure: dict) -> Dict:
        """Berechnet Jahresstatistiken"""
        if not months_data:
            return {}
        
        total_income = 0.0
        total_expenses = 0.0
        monthly_incomes = []
        monthly_expenses = []
        
        for month, month_data in months_data:
            totals = BudgetCalculator.calculate_totals(month_data, structure)
            total_income += totals['income']
            total_expenses += totals['expenses']
            monthly_incomes.append(totals['income'])
            monthly_expenses.append(totals['expenses'])
        
        num_months = len(months_data)
        
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'balance': total_income - total_expenses,
            'avg_income': total_income / num_months,
            'avg_expenses': total_expenses / num_months,
            'avg_balance': (total_income - total_expenses) / num_months,
            'monthly_incomes': monthly_incomes,
            'monthly_expenses': monthly_expenses
        }
    
    @staticmethod
    def forecast_trend(historical_data: List[float], periods: int = 3) -> Tuple[List[float], float, float]:
        """
        Berechnet Trendprognose mittels linearer Regression
        
        Args:
            historical_data: Historische Werte
            periods: Anzahl zu prognostizierender Perioden
        
        Returns:
            (prognostizierte_werte, trend_steigung, trend_achsenabschnitt)
        """
        if len(historical_data) < 2:
            return [historical_data[-1]] * periods if historical_data else [0] * periods, 0, 0
        
        x = np.arange(len(historical_data))
        coeffs = np.polyfit(x, historical_data, 1)
        trend_func = np.poly1d(coeffs)
        
        # Forecast
        future_x = np.arange(len(historical_data), len(historical_data) + periods)
        forecast = [trend_func(xi) for xi in future_x]
        
        return forecast, coeffs[0], coeffs[1]
    
    @staticmethod
    def check_budget_limit(amount: float, limit: float) -> Tuple[bool, float]:
        """
        Prüft ob Budget-Limit überschritten
        
        Returns:
            (is_exceeded, percentage)
        """
        if limit <= 0:
            return False, 0.0
        
        percentage = (amount / limit) * 100.0
        return amount > limit, percentage
