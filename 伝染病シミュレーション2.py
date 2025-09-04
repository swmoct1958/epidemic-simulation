import random
import argparse
import csv
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 日本語フォントの設定
# ご自身の環境に合わせてパスを修正してください
# Windowsの場合
font_path = 'C:\\Windows\\Fonts\\msgothic.ttc'
# Macの場合
# font_path = '/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc'
fp = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = fp.get_family()

class Agent:
    SUSCEPTIBLE = 0
    INFECTED = 1
    RECOVERED = 2

    def __init__(self, group_id):
        self.state = Agent.SUSCEPTIBLE
        self.group_id = group_id

def initialize_agents(N, G, seed=None):
    if seed is not None:
        random.seed(seed)
    return [Agent(group_id=random.randint(0, G - 1)) for _ in range(N)]

def infect(agent, agents, α_intra, α_inter):
    for neighbor in agents:
        if neighbor.state == Agent.INFECTED:
            α = α_intra if agent.group_id == neighbor.group_id else α_inter
            if random.random() < α:
                agent.state = Agent.INFECTED
                break

def run_simulation(N, G, α_intra, α_inter, ψ, steps, seed=None, output_file=None):
    agents = initialize_agents(N, G, seed)
    agents[random.randint(0, N - 1)].state = Agent.INFECTED  # 初期感染者

    history = []

    for t in range(steps):
        S = sum(1 for a in agents if a.state == Agent.SUSCEPTIBLE)
        I = sum(1 for a in agents if a.state == Agent.INFECTED)
        R = sum(1 for a in agents if a.state == Agent.RECOVERED)
        history.append({'Step': t, 'S': S, 'I': I, 'R': R})

        for agent in agents:
            if agent.state == Agent.SUSCEPTIBLE:
                infect(agent, agents, α_intra, α_inter)
            elif agent.state == Agent.INFECTED and random.random() < ψ:
                agent.state = Agent.RECOVERED

    if output_file:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['Step', 'S', 'I', 'R'])
            writer.writeheader()
            writer.writerows(history)

    return history

def plot_history(history):
    steps = [h['Step'] for h in history]
    susceptible = [h['S'] for h in history]
    infected = [h['I'] for h in history]
    recovered = [h['R'] for h in history]

    plt.plot(steps, susceptible, label='感受性者')
    plt.plot(steps, infected, label='感染者')
    plt.plot(steps, recovered, label='回復者')
    plt.xlabel('ステップ')
    plt.ylabel('人口')
    plt.title('感染症シミュレーション')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def main():
    plt.rcParams['font.family'] = 'Yu Gothic'
    parser = argparse.ArgumentParser(description='伝染病シミュレーション（グループ感染対応）')
    parser.add_argument('--N', type=int, default=1000, help='総エージェント数')
    parser.add_argument('--G', type=int, default=10, help='グループ数')
    parser.add_argument('--steps', type=int, default=100, help='シミュレーションステップ数')
    parser.add_argument('--alpha_intra', type=float, default=0.05, help='同一グループ内の感染率')
    parser.add_argument('--alpha_inter', type=float, default=0.005, help='異なるグループ間の感染率')
    parser.add_argument('--psi', type=float, default=0.01, help='回復率')
    parser.add_argument('--seed', type=int, default=None, help='乱数シード（任意）')
    parser.add_argument('--output', type=str, default='simulation_output.csv', help='CSV出力ファイル名')
    parser.add_argument('--plot', action='store_true', help='感染者数の推移をグラフ表示する')

    args = parser.parse_args()

    history = run_simulation(
        N=args.N,
        G=args.G,
        α_intra=args.alpha_intra,
        α_inter=args.alpha_inter,
        ψ=args.psi,
        steps=args.steps,
        seed=args.seed,
        output_file=args.output
    )

    if args.plot:
        plot_history(history)

if __name__ == '__main__':
    main()