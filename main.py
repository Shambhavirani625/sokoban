from copy import deepcopy

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = "secret-key"

LEVELS = {}

for i in range(1, 6):
    with open(f"sokoban/level{i}.txt") as file:
        lines = file.readlines()
        LEVELS[i] = list(list(line.strip()) for line in lines)


class SokobanGame:
    def __init__(self, level):
        self.level = deepcopy(level)
        self._get_cords()

    def _get_cords(self):
        self.player, self.blocks, self.target = [], [], []
        for i, row in enumerate(self.level):
            for j, val in enumerate(row):
                if val == "@":
                    self.player = [i, j]
                if val in ("$", "x"):
                    self.blocks.append([i, j])
                if val in (".", "x"):
                    self.target.append([i, j])

    def _move(self, dx, dy):
        x, y = self.player
        nx, ny = x + dx, y + dy
        nnx, nny = x + 2 * dx, y + 2 * dy

        if not (0 <= nx < len(self.level) and 0 <= ny < len(self.level[0])):
            return
        next_tile = self.level[nx][ny]
        next_next_tile = (
            self.level[nnx][nny]
            if 0 <= nnx < len(self.level) and 0 <= nny < len(self.level[0])
            else "#"
        )

        if next_tile in (" ", "."):
            self.level[nx][ny] = "@"
            self.level[x][y] = "." if [x, y] in self.target else " "
            self.player = [nx, ny]
        elif next_tile in ("$", "x") and next_next_tile in (" ", "."):
            self.level[nx][ny] = "@"
            self.level[nnx][nny] = "x" if next_next_tile == "." else "$"
            self.level[x][y] = "." if [x, y] in self.target else " "
            self.player = [nx, ny]

    def move(self, direction):
        moves = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
        if direction in moves:
            self._move(*moves[direction])

    def display(self):
        mapping = {"#": "⬛", "@": "🙂", " ": "⬜", "$": "📦", ".": "🎯", "x": "✅"}
        return "\n".join(
            "".join(mapping.get(ch, ch) for ch in row) for row in self.level
        )

    def is_game_over(self):
        return all(self.level[x][y] == "x" for x, y in self.target)


@app.route("/")
def index():
    level_num = int(request.args.get("level", 1))
    if level_num not in LEVELS:
        level_num = 1
    session["level_num"] = level_num
    session["level"] = deepcopy(LEVELS[level_num])
    return render_template("game.html", level=level_num)


@app.route("/state", methods=["GET"])
def state():
    game = SokobanGame(session["level"])
    return jsonify({"board": game.display(), "game_over": game.is_game_over()})


@app.route("/move", methods=["POST"])
def move():
    direction = request.json.get("direction")
    game = SokobanGame(session["level"])
    game.move(direction)
    session["level"] = game.level
    return jsonify ({"board": game.display(), "game_over": game.is_game_over()})


@app.route("/reset")
def reset():
    level_num = session.get("level_num", 1)
    session["level"] = deepcopy(LEVELS[level_num])
    return redirect(url_for("index", level=level_num))


if __name__ == "__main__":
    app.run(debug=True)
