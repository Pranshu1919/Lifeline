"""
LifeLine ML Module 4: Mixed-Integer Linear Programming (MILP) Resource Dispatch Solver
Author: ML Engineer 2
Description: Formulates and solves the optimal emergency unit assignment problem to minimize overall weighted response time.
"""

from scipy.optimize import milp, LinearConstraint, Bounds
import numpy as np

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1))*np.cos(np.radians(lat2))*np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

def solve_dispatch(incidents, units):
    """
    incidents: list of dicts [{'id': 'INC1', 'lat': ..., 'lon': ..., 'severity': 4.5}]
    units: list of dicts [{'id': 'U1', 'lat': ..., 'lon': ..., 'speed': 30}]
    """
    n_inc = len(incidents)
    n_units = len(units)
    
    if n_inc == 0 or n_units == 0:
        return []

    # Calculate travel times matrix t_uk (in minutes)
    cost_vector = []
    for u_idx, u in enumerate(units):
        for k_idx, k in enumerate(incidents):
            dist_km = haversine(u['lat'], u['lon'], k['lat'], k['lon'])
            travel_time_mins = (dist_km / u.get('speed', 30)) * 60.0
            # Objective: Weight response time by inverse of severity
            weighted_cost = travel_time_mins / k['severity']
            cost_vector.append(weighted_cost)
            
    c = np.array(cost_vector)
    n_vars = len(c)
    integrality = np.ones(n_vars) # All binary variables

    # Constraint 1: Each vehicle u dispatched to at most 1 incident (sum_k x_uk <= 1)
    A_rows = []
    b_upper = []
    b_lower = []
    
    for u_idx in range(n_units):
        row = np.zeros(n_vars)
        for k_idx in range(n_inc):
            var_idx = u_idx * n_inc + k_idx
            row[var_idx] = 1.0
        A_rows.append(row)
        b_lower.append(0.0)
        b_upper.append(1.0)
        
    constraints = LinearConstraint(np.array(A_rows), b_lower, b_upper)
    bounds = Bounds(0, 1)

    res = milp(c=c, integrality=integrality, constraints=constraints, bounds=bounds)

    dispatch_plan = []
    if res.success:
        x_sol = res.x
        for u_idx in range(n_units):
            for k_idx in range(n_inc):
                var_idx = u_idx * n_inc + k_idx
                if x_sol[var_idx] > 0.5:
                    u = units[u_idx]
                    k = incidents[k_idx]
                    dist_km = haversine(u['lat'], u['lon'], k['lat'], k['lon'])
                    travel_time_mins = round((dist_km / u.get('speed', 30)) * 60.0, 1)
                    dispatch_plan.append({
                        'unit_id': u['id'],
                        'incident_id': k['id'],
                        'estimated_travel_time_mins': travel_time_mins,
                        'xai_explanation': f"Unit {u['id']} dispatched to {k['id']}: Travel time {travel_time_mins} mins, severity {k['severity']} prioritized."
                    })
                    
    return dispatch_plan

if __name__ == '__main__':
    sample_incidents = [
        {'id': 'INC-001', 'lat': 28.6752, 'lon': 77.5020, 'severity': 4.5},
        {'id': 'INC-002', 'lat': 28.6900, 'lon': 77.5200, 'severity': 2.0}
    ]
    sample_units = [
        {'id': 'AMBULANCE-01', 'lat': 28.6800, 'lon': 77.4950, 'speed': 35},
        {'id': 'RESCUE-BOAT-01', 'lat': 28.6710, 'lon': 77.5100, 'speed': 20}
    ]
    
    plan = solve_dispatch(sample_incidents, sample_units)
    print("=== MILP Solver Verification Test ===")
    print("Optimization Plan Generated:", plan)
