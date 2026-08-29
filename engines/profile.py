def num_to_word(n):
    words = {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five', 
             6: 'Six', 7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten'}
    return words.get(n, str(n)).capitalize()

def build_profile(customer):
    assets = sum(customer.get("assets", {}).values())
    liabilities = sum(l.get("outstanding", 0) for l in customer.get("liabilities", []))
    net_worth = assets - liabilities
    
    monthly_income = customer.get("monthly_income", 0)
    
    transactions = customer.get("transactions", [])
    if transactions:
        all_months = sorted(list(set(t["date"][:7] for t in transactions)))
        last_12_months = set(all_months[-12:])
        filtered_transactions = [t for t in transactions if t["date"][:7] in last_12_months]
        num_months = len(last_12_months)
    else:
        filtered_transactions = []
        num_months = 1
    
    expense_breakdown = {}
    for t in filtered_transactions:
        cat = t["category"]
        expense_breakdown[cat] = expense_breakdown.get(cat, 0) + t["amount"]
        
    for cat in expense_breakdown:
        expense_breakdown[cat] = int(round(expense_breakdown[cat] / num_months))
        
    monthly_expense = sum(expense_breakdown.values())
    
    total_raw = sum(t["amount"] for t in filtered_transactions)
    true_mean = int(round(total_raw / num_months))
    diff = true_mean - monthly_expense
    if diff != 0 and expense_breakdown:
        largest_cat = max(expense_breakdown, key=expense_breakdown.get)
        expense_breakdown[largest_cat] += diff
        monthly_expense = true_mean

    monthly_surplus = monthly_income - monthly_expense
    existing_emi_total = sum(l.get("emi", 0) for l in customer.get("liabilities", []))
    
    savings = customer.get("assets", {}).get("savings_account", 0)
    emergency_fund_months = round(savings / monthly_expense, 1) if monthly_expense else 0.0
    
    score = 0
    reasons = []
    
    # 1. Surplus
    surplus_ratio = monthly_surplus / monthly_income if monthly_income else 0
    if surplus_ratio >= 0.30:
        score += 2
        reasons.append(f"Monthly surplus of {int(surplus_ratio*100)}% of income is healthy")
    elif surplus_ratio >= 0.15:
        score += 1
        reasons.append(f"Monthly surplus of {int(surplus_ratio*100)}% provides some cushion")
    else:
        score += 0
        reasons.append(f"Monthly surplus of {int(surplus_ratio*100)}% leaves little room for error")
        
    # 2. Emergency fund
    if emergency_fund_months >= 6:
        score += 2
        reasons.append(f"Emergency fund of {emergency_fund_months} months provides strong protection")
    elif emergency_fund_months >= 3:
        score += 1
        reasons.append(f"Emergency fund of {emergency_fund_months} months is adequate")
    else:
        score += 0
        if emergency_fund_months < 0.5:
            reasons.append("Emergency fund covers less than half a month of expenses")
        else:
            reasons.append(f"Emergency fund of {emergency_fund_months} months is below the recommended 3 months")
            
    # 3. Dependents & liabilities
    dependents = customer.get("dependents", 0)
    dep_score = 2 if dependents == 0 else (1 if dependents <= 2 else 0)
    score += dep_score
    
    active_loans = [l["type"].replace("_", " ") for l in customer.get("liabilities", []) if l.get("outstanding", 0) > 0]
    
    if dependents > 0 or active_loans:
        dep_str = f"{num_to_word(dependents)} dependent{'s' if dependents > 1 else ''}" if dependents > 0 else "No dependents"
        loan_str = f"an active {active_loans[0]}" if active_loans else ""
        if dependents > 0 and active_loans:
            reasons.append(f"{dep_str} and {loan_str} reduce room for loss")
        elif active_loans:
            reasons.append(f"Active {active_loans[0]} reduces room for loss")
        elif dependents > 0:
            reasons.append(f"{dep_str} reduce{'s' if dependents == 1 else ''} room for loss")
            
    # 4. Shortest goal horizon
    goals = customer.get("goals", [])
    if goals:
        shortest_goal = min(g["years"] for g in goals)
        if shortest_goal >= 10:
            score += 2
            reasons.append(f"{num_to_word(shortest_goal)} year horizon allows time to ride out market cycles")
        elif shortest_goal >= 5:
            score += 1
            reasons.append(f"{num_to_word(shortest_goal)} year horizon is long enough to recover from a single bad year")
        else:
            score += 0
            reasons.append(f"{num_to_word(shortest_goal)} year horizon limits ability to recover from short-term losses")
            
    # 5. Employment
    emp = customer.get("employment_type", "")
    if emp == "salaried":
        score += 1
        
    if len(reasons) < 3:
        if dependents == 0 and not active_loans:
            reasons.append("No dependents or active loans maximizes room for loss")
            
    if len(reasons) < 3:
        if emp == "salaried":
            reasons.append("Stable salaried income improves risk capacity")
        else:
            reasons.append("Non-salaried income requires a higher safety margin")
        
    if score >= 7:
        risk_capacity = "aggressive"
    elif score >= 4:
        risk_capacity = "moderate"
    else:
        risk_capacity = "conservative"
        
    return {
        "net_worth": net_worth,
        "total_assets": assets,
        "total_liabilities": liabilities,
        "monthly_income": monthly_income,
        "monthly_expense": monthly_expense,
        "monthly_surplus": monthly_surplus,
        "existing_emi_total": existing_emi_total,
        "emergency_fund_months": emergency_fund_months,
        "risk_capacity": risk_capacity,
        "risk_capacity_reasons": reasons,
        "expense_breakdown": expense_breakdown
    }
