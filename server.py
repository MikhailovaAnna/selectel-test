from datetime import datetime
from flask import Flask, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from sqlalchemy import MetaData

from config import PGConfig, API_PATH, TICKET_PATH, TEST_USER, COMMENT_PATH, state_transitions, TicketState


# Настройка приложения
DB_URL = 'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}'.format(user=PGConfig.PG_USER,
                                                                             password=PGConfig.PG_PASSWD,
                                                                             host=PGConfig.PG_HOST,
                                                                             port=PGConfig.PG_PORT,
                                                                             db=PGConfig.PG_DATABASE)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config.from_object('config.CacheConfig')
metadata = MetaData(schema='TEST', naming_convention={"ix": "ix_%(column_0_label)s",
                                                      "uq": "uq_%(table_name)s_%(column_0_name)s",
                                                      "ck": "ck_%(table_name)s_%(constraint_name)s",
                                                      "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
                                                      "pk": "pk_%(table_name)s"})
db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db)
cache = Cache(app)


# Модели таблиц
class TicketModel(db.Model):
    __tablename__ = 'ticket'

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    name = db.Column(db.String(200), unique=False, nullable=False)
    description = db.Column(db.Text(), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False)
    state = db.Column(db.String(10), unique=False, nullable=False, default='OPEN')

    def __repr__(self):
        return '<Ticket %r>' % self.name


class CommentModel(db.Model):
    __tablename__ = 'comment'

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    text = db.Column(db.Text(), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False)

    ticket = db.relationship('TicketModel', backref=db.backref('ticket', lazy=True))

    def __repr__(self):
        return '<Comment %r>' % self.text


# Обработка получения информации о тикете и обновление тикета
@app.route(f'/{API_PATH}/{TICKET_PATH}/<int:ticket_id>', methods=['GET', 'PUT'])
@cache.cached(timeout=30)
def handle_ticket(ticket_id):
    ticket = TicketModel.query.get_or_404(ticket_id)

    if request.method == 'GET':
        response = {
            "name": ticket.name,
            "description": ticket.description,
            "email": ticket.email,
            "state": ticket.state,
            "created": ticket.created,
            "updated": ticket.updated,
            "comments": [dict(text=comment.text, created=comment.created, email=comment.email) for comment in
                         CommentModel.query.filter(CommentModel.ticket_id == ticket_id).all()]
        }
        return {"message": "success", "data": response}
    elif request.method == 'PUT':
        data = request.get_json()
        if state := data.get('state'):
            if state in state_transitions.get(ticket.state):
                ticket.state = state
                ticket.updated = datetime.utcnow()
                db.session.add(ticket)
                db.session.commit()
                return {"message": f"Ticket {ticket.name} successfully updated (new state - {state})."}
            else:
                return {"error": "This state transition not awaited."}
        else:
            return {"error": "Only ticket's state can be modified."}


# Создание тикета
@app.route(f'/{API_PATH}/{TICKET_PATH}', methods=['POST'])
def create_ticket():
    if request.method == 'POST':
        data = request.get_json()
        new_ticket = TicketModel(name=data['name'],
                                 description=data['description'],
                                 email=TEST_USER)
        db.session.add(new_ticket)
        db.session.commit()
        return {"message": f"Ticket {new_ticket.name} has been created successfully."}


# Добавление комментария к тикету
@app.route(f'/{API_PATH}/{TICKET_PATH}/<int:ticket_id>/{COMMENT_PATH}', methods=['POST'])
def handle_comment(ticket_id):
    ticket = TicketModel.query.get_or_404(ticket_id)

    if request.method == 'POST':
        if ticket.state != TicketState.closed.value:
            data = request.get_json()
            new_comment = CommentModel(text=data['text'],
                                       ticket_id=ticket_id,
                                       email=TEST_USER)
            db.session.add(new_comment)
            db.session.commit()
            ticket.updated = datetime.utcnow()
            db.session.add(ticket)
            db.session.commit()
            return {"message": f"Comment {new_comment.text} for {ticket_id} ticket has been created successfully."}
        else:
            return {"error": "Comment can be added only in unclosed tickets."}


if __name__ == "__main__":
    app.run(debug=True)
