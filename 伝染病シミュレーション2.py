import random
import argparse
import csv

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
        history.append([t, S, I, R])

        for agent in agents:
            if agent.state == Agent.SUSCEPTIBLE:
                infect(agent, agents, α_intra, α_inter)
            elif agent.state == Agent.INFECTED and random.random() < ψ:
                agent.state = Agent.RECOVERED

    if output_file:
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Step', 'Susceptible', 'Infected', 'Recovered'])
            writer.writerows(history)

    return history

def main():
    parser = argparse.ArgumentParser(description='伝染病シミュレーション（グループ感染対応）')
    parser.add_argument('--N', type=int, default=1000, help='総エージェント数')
    parser.add_argument('--G', type=int, default=10, help='グループ数')
    parser.add_argument('--steps', type=int, default=100, help='シミュレーションステップ数')
    parser.add_argument('--α_intra', type=float, default=0.05, help='同一グループ内の感染率')
    parser.add_argument('--α_inter', type=float, default=0.005, help='異なるグループ間の感染率')
    parser.add_argument('--ψ', type=float, default=0.01, help='回復率')
    parser.add_argument('--seed', type=int, default=None, help='乱数シード（任意）')
    parser.add_argument('--output', type=str, default='simulation_output.csv', help='CSV出力ファイル名')

    args = parser.parse_args()

    run_simulation(
        N=args.N,
        G=args.G,
        α_intra=args.α_intra,
        α_inter=args.α_inter,
        ψ=args.ψ,
        steps=args.steps,
        seed=args.seed,
        output_file=args.output
    )

if __name__ == '__main__':
    main()
