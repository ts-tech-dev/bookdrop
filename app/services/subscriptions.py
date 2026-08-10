from sqlalchemy.orm import Session

from app.models import Author, AuthorSubscription, User


def subscribe_user_to_all_authors(db: Session, user: User) -> None:
    for author in db.query(Author).all():
        db.add(AuthorSubscription(user_id=user.id, author_id=author.id))
    db.commit()


def subscribe_all_users_to_author(db: Session, author: Author) -> None:
    for user in db.query(User).all():
        db.add(AuthorSubscription(user_id=user.id, author_id=author.id))
    db.commit()
