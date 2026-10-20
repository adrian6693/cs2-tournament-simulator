# 🏆 CS2 Tournament Manager

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![GUI Framework](https://img.shields.io/badge/GUI-PySide6-green.svg)
![License](https://img.shields.io/badge/license-MIT-informational.svg)

**CS2 Tournament Manager** is a desktop application built with **PySide6 (Qt for Python)** designed to organize, manage, and simulate Counter-Strike 2 tournaments. It allows you to manage team rosters, generate automatic matchups based on *seeding*, record match results, view interactive *brackets*, and maintain a global leaderboard tracking accumulated points.

---

## 🛠️ Built With

* **Python 3.10+**
* **PySide6** (Qt6-based graphical user interface)
* **JSON** (Local data storage)

---

## 🚀 Getting Started

### Prerequisites

Make sure you have Python 3.10 or higher installed on your system.

### Installation & Execution

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/cs2-tournament-simulator.git
   cd cs2-tournament-simulator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

---

## ✨ Features

### 👥 Team Management
* Create a global roster of teams with custom **names** and **tags**.
* Individual team profile pages accessible from the main list or rankings.
* Advanced team statistics and a **trophy cabinet** showcasing images of won tournaments.

### ⚙️ Tournament Creator (4-Step Wizard)
1. **Basic Info:** Name, date, and importance multiplier (Local, Regional, National, International, Major, or custom).
2. **Tournament Format:** Configure 1 or 2 combinable stages.
   * *Round Robin (League):* Split teams into multiple groups (Group A, Group B, etc.) distributed in a serpentine pattern based on *seed* for balanced groups.
   * *Match Format:* Choose Best-of series length (Bo1, Bo3, Bo5...).
   * *Stage Transition:* Define how many teams advance from Stage 1 to Stage 2.
3. **Participants & Seeding:** Select participating teams and adjust *seed* ordering (ensuring top seeds meet as late as possible in elimination brackets).
4. **Points Table & Rewards:** Customizable points allocation based on final placement (pre-filled with editable templates) and optional **trophy image** upload for the champion.

### 🎮 Match Management & Workflow
* **Stage Tabs:** Dedicated tab for each active stage of the tournament.
* **Interactive Brackets:** Graphical bracket view for *Single Elimination*. Click any match to enter scores.
* **Round-by-Round Views:** Organised round views with editable scoreboards for *Round Robin* and *Swiss* formats.
* **Advance Stage / Finalize:** Automatic seeding transfer of qualified teams to the next stage, or tournament completion with automated points distribution.
* **🎲 Randomize Pending Matches:** Quick button to fill all unplayed matches with random realistic scores without altering existing results (ideal for full tournament simulations).

### 📊 Global Leaderboard & Stats
* Master standings table accumulating points earned across all completed tournaments.
* Detailed stats and team history: *Tournaments played/won, podium finishes, total points, match record, win rate %, and past tournament history*.

---

## 🎮 Supported Tournament Formats

| Format | Description |
| :--- | :--- |
| **Round Robin** | All-vs-all format (single or double round robin). Supports multi-group split with combined standings. |
| **Single Elimination** | Traditional bracket with standard seeding and automatic *byes* if team count isn't a power of 2. |
| **Swiss System** | First round seeded by halves; subsequent rounds pair teams with identical records while avoiding repeat matchups where possible. |

---

## 💾 Data Storage

All persistent data is stored locally in JSON format within the `data/` directory:

```text
data/
├── teams.json           # Global team roster
└── tournaments/         # Individual tournament files
    └── <tournament_id>.json # Tournament settings, stages, matches, results, and final standings
```

---

## 🗺️ Roadmap & Future Ideas

- [ ] Support for **Double Elimination** brackets (Losers Bracket).
- [ ] Ability to edit/add teams to an ongoing tournament.
- [ ] Export rankings or brackets as images (PNG) or PDF.
- [ ] Custom team logo support.

---

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.