from flask import Flask, render_template, url_for, flash, redirect, request, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from models import db, bcrypt, login_manager, User, GameRequest, Game
from game_logic import TicTacToe

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/')
@app.route('/home')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Ваша учетная запись создана! Теперь вы можете войти в систему', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=True)
            return redirect(url_for('home'))
        else:
            flash('Войти не удалось. Пожалуйста, проверьте адрес электронной почты и пароль', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/send_request/<int:user_id>')
@login_required
def send_request(user_id):
    user = User.query.get(user_id)
    if user:
        game_request = GameRequest(sender_id=current_user.id, receiver_id=user_id)
        db.session.add(game_request)
        db.session.commit()
        flash('Запрос на игру отправлен!', 'success')
    else:
        flash('Пользователь не найден.', 'danger')
    return redirect(url_for('home'))


@app.route('/accept_request/<int:request_id>')
@login_required
def accept_request(request_id):
    game_request = GameRequest.query.get(request_id)
    if game_request and game_request.receiver_id == current_user.id:
        game_request.status = 'accepted'
        game = Game(player1_id=game_request.sender_id, player2_id=current_user.id, current_turn=game_request.sender_id)
        db.session.add(game)
        db.session.commit()
        flash('Заявка на игру принята!', 'success')
    else:
        flash('Запрос на игру не найден.', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/game/<int:game_id>')
@login_required
def game(game_id):
    game = Game.query.get(game_id)
    if game and (game.player1_id == current_user.id or game.player2_id == current_user.id):
        opponent_id = game.player1_id if game.player2_id == current_user.id else game.player2_id
        opponent = User.query.get(opponent_id)
        tic_tac_toe = TicTacToe(game.board)
        return render_template('game.html', game=game, board=tic_tac_toe.board, opponent=opponent)
    else:
        flash('Game not found or access denied.', 'danger')
        return redirect(url_for('home'))



@app.route('/make_move/<int:game_id>', methods=['POST'])
@login_required
def make_move(game_id):
    game = Game.query.get(game_id)
    if game and (game.player1_id == current_user.id or game.player2_id == current_user.id):
        if game.is_finished:
            return jsonify({'status': 'failure', 'message': 'Game is already finished'})
        
        data = request.get_json()
        square = data['square']
        tic_tac_toe = TicTacToe(game.board)
        if game.current_turn == current_user.id and tic_tac_toe.make_move(square, 'X' if game.player1_id == current_user.id else 'O'):
            game.board = tic_tac_toe.get_board_string()
            if tic_tac_toe.current_winner:
                game.winner_id = current_user.id
                game.is_finished = True
                db.session.commit()
                return jsonify({'status': 'success', 'board': game.board, 'winner': current_user.username})
            game.current_turn = game.player2_id if game.current_turn == game.player1_id else game.player1_id
            db.session.commit()
            return jsonify({'status': 'success', 'board': game.board})
    return jsonify({'status': 'failure'})


@app.route('/dashboard')
@login_required
def dashboard():
    users = User.query.filter(User.id != current_user.id).all()
    received_requests = GameRequest.query.filter_by(receiver_id=current_user.id, status='pending').all()
    games = Game.query.filter(
        ((Game.player1_id == current_user.id) | (Game.player2_id == current_user.id)) & (Game.is_finished == False)
    ).all()
    
    finished_games = Game.query.filter(
        ((Game.player1_id == current_user.id) | (Game.player2_id == current_user.id)) & (Game.is_finished == True)
    ).all()
    
    ongoing_games = []
    for game in games:
        opponent_id = game.player1_id if game.player2_id == current_user.id else game.player2_id
        opponent = User.query.get(opponent_id)
        ongoing_games.append({
            'id': game.id,
            'opponent': opponent
        })

    finished_games_list = []
    for game in finished_games:
        opponent_id = game.player1_id if game.player2_id == current_user.id else game.player2_id
        opponent = User.query.get(opponent_id)
        finished_games_list.append({
            'id': game.id,
            'opponent': opponent,
            'winner_id': game.winner_id
        })

    return render_template('dashboard.html', users=users, received_requests=received_requests, games=ongoing_games, finished_games=finished_games_list)


if __name__ == '__main__':
    app.run(debug=True)

