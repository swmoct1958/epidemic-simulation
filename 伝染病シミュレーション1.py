import numpy as np
import random
import argparse
import sys
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# --- 日本語フォントの設定 ---
def set_japanese_font():
    font_paths = [
        "C:/Windows/Fonts/meiryo.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
        "/usr/local/share/fonts/NotoSansCJKjp-Regular.otf",
    ]
    font_path = None
    for path in font_paths:
        if fm.findfont(fm.FontProperties(fname=path)):
            font_path = path
            break
            
    if font_path:
        fm.fontManager.addfont(font_path)
        plt.rcParams["font.family"] = fm.FontProperties(fname=font_path).get_name()
        print("日本語フォントが設定されました。")
    else:
        print("日本語フォントが見つかりませんでした。ワーニングが発生する可能性があります。")

# --- 定数とクラス定義 ---
Z, A, B, DEATH = 0, 1, 2, -1

class Agent:
    def __init__(self, state, infection_time=-1):
        self.state = state
        self.infection_time = infection_time

# --- パラメータ設定と読み込み ---
def parse_arguments():
    parser = argparse.ArgumentParser(description='伝染病シミュレーション')
    parser.add_argument('-f', '--file', type=str, help='パラメータ設定ファイル')
    parser.add_argument('-n', '--field_num', type=int, choices=[1, 2], default=2, help='フィールドの数 (1 or 2)')
    parser.add_argument('-a', '--alfa', type=float, default=0.1, help='罹患率α')
    parser.add_argument('-y', '--psi', type=float, default=0.05, help='回復率ψ')
    parser.add_argument('-b', '--beta', type=float, default=0.02, help='移動率β')
    parser.add_argument('-w', '--omega', type=float, default=0.01, help='移動率ω')
    parser.add_argument('-p', '--pi', type=float, default=0.01, help='F2a->F2b移動率π')
    parser.add_argument('-r', '--rho', type=float, default=0.01, help='F2b->F2a移動率ρ')
    parser.add_argument('-iz', '--initial_Z', type=int, default=5000, help='健常者Zの初期数')
    parser.add_argument('-ia', '--initial_A', type=int, default=100, help='罹患者Aの初期数')
    parser.add_argument('-ib', '--initial_B', type=int, default=100, help='罹患者Bの初期数')
    parser.add_argument('-t1', '--t1', type=int, default=200, help='イベントt1の発生時間')
    parser.add_argument('-t2', '--t2', type=int, default=800, help='B個体の生存期間')
    parser.add_argument('-mt', '--max_time', type=int, default=1000, help='シミュレーションの最大時間')
    parser.add_argument('-gs', '--grid_size', type=int, default=100, help='フィールドの一辺のサイズ')

    args = parser.parse_args()
    
    params = vars(args)
    
    if args.file:
        try:
            with open(args.file, 'r') as f:
                param_map = {
                    'n': 'field_num', 'alfa': 'alfa', 'psi': 'psi', 'beta': 'beta',
                    'omega': 'omega', 'pi': 'pi', 'rho': 'rho',
                    'initial_Z': 'initial_Z', 'initial_A': 'initial_A', 'initial_B': 'initial_B',
                    't1': 't1', 't2': 't2', 'max_time': 'max_time', 'grid_size': 'grid_size'
                }
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    try:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().split('#')[0].strip()
                        if key in param_map:
                            attr_name = param_map[key]
                            arg_type = [a for a in parser._actions if a.dest == attr_name][0].type
                            params[attr_name] = arg_type(value)
                    except (ValueError, IndexError):
                        print(f"警告: パラメータファイルの行の書式が不正です。'{line}'", file=sys.stderr)
        except FileNotFoundError:
            print(f"エラー: 指定されたファイル '{args.file}' が見つかりません。", file=sys.stderr)
            sys.exit(1)
            
    return params

# --- シミュレーション本体 ---
def run_simulation(params):
    alpha = params['alfa']
    psi = params['psi']
    beta = params['beta']
    omega = params['omega']
    pi = params['pi']
    rho = params['rho']
    field_num = int(params['field_num'])
    
    GRID_SIZE = params['grid_size']
    MAX_TIME = params['max_time']
    t1 = params['t1']
    t2 = params['t2']
    
    TOTAL_POPULATION = GRID_SIZE * GRID_SIZE
    
    initial_total = params['initial_Z'] + params['initial_A'] + params['initial_B']
    if initial_total > TOTAL_POPULATION:
        print("エラー: 初期個体数の合計が総人口を超えています。", file=sys.stderr)
        sys.exit(1)
    
    initial_states = [Z] * int(params['initial_Z']) + [A] * int(params['initial_A']) + [B] * int(params['initial_B'])
    initial_states += [Z] * (TOTAL_POPULATION - initial_total)
    random.shuffle(initial_states)
    
    if field_num == 1:
        field = np.full((GRID_SIZE, GRID_SIZE), None, dtype=object)
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                field[i, j] = Agent(initial_states.pop())
    else:
        field_a = np.full((GRID_SIZE, GRID_SIZE), None, dtype=object)
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                field_a[i, j] = Agent(Z)
        
        field_b = np.full((GRID_SIZE, GRID_SIZE), None, dtype=object)
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                field_b[i, j] = Agent(initial_states.pop())

    z_counts, a_counts, b_counts, time_steps = [], [], [], []

    for t in range(MAX_TIME):
        def check_for_death(f):
            for i in range(GRID_SIZE):
                for j in range(GRID_SIZE):
                    agent = f[i, j]
                    if agent.state == B and t - agent.infection_time >= t2:
                        agent.state = DEATH
        
        if field_num == 1:
            check_for_death(field)
        else:
            check_for_death(field_b)
            
        for _ in range(TOTAL_POPULATION):
            if field_num == 1:
                x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
                agent = field[x, y]
            else:
                x, y = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
                agent = field_b[x, y]

            if agent.state == DEATH:
                continue
            
            neighbors = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0: continue
                    nx, ny = (x + dx) % GRID_SIZE, (y + dy) % GRID_SIZE
                    if field_num == 1:
                        neighbors.append(field[nx, ny].state)
                    else:
                        neighbors.append(field_b[nx, ny].state)

            if agent.state == Z and A in neighbors and random.random() < alpha:
                agent.state = A
            elif agent.state == A:
                if random.random() < psi:
                    agent.state = Z
                elif random.random() < beta:
                    agent.state = B
                    agent.infection_time = t
            elif agent.state == B and random.random() < omega:
                agent.state = A
                agent.infection_time = -1
        
        if t == t1:
            if field_num == 1:
                for i in range(GRID_SIZE):
                    for j in range(GRID_SIZE):
                        if field[i, j].state == Z and random.random() < 0.05:
                            field[i, j].state = B
                            field[i, j].infection_time = t
            else:
                for i in range(GRID_SIZE):
                    for j in range(GRID_SIZE):
                        if field_b[i, j].state == Z and random.random() < 0.05:
                            field_b[i, j].state = B
                            field_b[i, j].infection_time = t

        if field_num == 2:
            all_agents_a = field_a.flatten()
            all_agents_b = field_b.flatten()
            
            z_agents_a = [agent for agent in all_agents_a if agent.state == Z]
            if z_agents_a:
                z_move_count = int(len(z_agents_a) * pi)
                agents_to_move = random.sample(z_agents_a, min(z_move_count, len(z_agents_a)))
                for agent in agents_to_move:
                    agent.state = DEATH
                    field_b[random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)] = Agent(Z)

            ab_agents_b = [agent for agent in all_agents_b if agent.state in [A, B]]
            if ab_agents_b:
                ab_move_count = int(len(ab_agents_b) * rho)
                agents_to_move = random.sample(ab_agents_b, min(ab_move_count, len(ab_agents_b)))
                for agent in agents_to_move:
                    agent.state = DEATH
                    field_a[random.randint(0, GRID_SIZE-1), random.randint(0, GRID_SIZE-1)] = Agent(agent.state, agent.infection_time)

        def count_agents(f):
            states = [agent.state for agent in f.flatten()]
            return states.count(Z), states.count(A), states.count(B)

        if field_num == 1:
            total_z, total_a, total_b = count_agents(field)
        else:
            total_z_a, total_a_a, total_b_a = count_agents(field_a)
            total_z_b, total_a_b, total_b_b = count_agents(field_b)
            total_z, total_a, total_b = total_z_a + total_z_b, total_a_a + total_a_b, total_b_a + total_b_b

        z_counts.append(total_z)
        a_counts.append(total_a)
        b_counts.append(total_b)
        time_steps.append(t)
        
        if total_b == 0 and t > t2:
            print(f"Bの個体がt={t}で消滅しました。シミュレーションを終了します。")
            break
            
    return time_steps, z_counts, a_counts, b_counts

# --- メイン実行部分 ---
if __name__ == "__main__":
    set_japanese_font()
    params = parse_arguments()
    print("以下のパラメータでシミュレーションを実行します:")
    print(params)
    time_steps, z_counts, a_counts, b_counts = run_simulation(params)
    
    results = np.column_stack([time_steps, z_counts, a_counts, b_counts])
    header = 'time,Z_count,A_count,B_count'
    np.savetxt('simulation_results.csv', results, delimiter=',', header=header, comments='')
    print("\nシミュレーション結果を 'simulation_results.csv' に保存しました。")

    plt.plot(time_steps, z_counts, label='健常者 (Z)')
    plt.plot(time_steps, a_counts, label='罹患者A')
    plt.plot(time_steps, b_counts, label='罹患者B')
    plt.xlabel('時間ステップ')
    plt.ylabel('個体数')
    plt.title('伝染病シミュレーションの推移')
    plt.legend()
    plt.grid(True)
    plt.show()
