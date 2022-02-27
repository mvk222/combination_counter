import pandas as pd
from itertools import combinations
from flask import send_file

class CombinationCounter():

    def count_combinations(self, path):
        df = pd.read_excel(f"files_to_process/{path}")
        df = df[['VPN','Var1','Var2']]
        df.columns = ['Versuchspersonennummer','Item','Gruppe']
        df = df.pivot_table(values='Item',
                        index=['Versuchspersonennummer','Gruppe'],
                        aggfunc=lambda x:sorted(list(x))).reset_index()
        base={}
        for index, row in df.iterrows():
            x_ = [(row['Versuchspersonennummer'],row['Gruppe'])]
            x_value =row['Item']
            combs=[]
            for L in range(1, 8):
                for subset in combinations(x_value, L):
                    combs.append(str(sorted(subset)))
            gruppe=list((x_, )) * len(combs)
            row_base = dict(zip(combs,gruppe))
            base={k: (base.get(k) if base.get(k) else []) + (row_base.get(k) if row_base.get(k) else []) for k in set(base) | set(row_base)}

        comb=[]
        occurance=[]
        count=[]
        for key, value in base.items():
            comb.append(key)
            occurance.append(str(value))
            count.append(len(value))
        result = pd.DataFrame({"kombination":comb,"auftreten":occurance,"count":count})
        result[result['count']>3].sort_values('count',ascending=False).reset_index(drop=True).to_csv(f"files_to_process/{path}.csv")