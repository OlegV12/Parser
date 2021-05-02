import sqlalchemy.exc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import models


class Database:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        models.Base.metadata.create_all(bind=self.engine)
        self.maker = sessionmaker(bind=self.engine)

    def get_or_create(self, session, model, **kwargs):
        model_instance = session.query(model).filter_by(**kwargs).first()
        if model_instance:
            return model_instance
        else:
            model_instance = model(**kwargs)
            return model_instance

    def add_post(self, data):
        session = self.maker()
        post = self.get_or_create(session, models.Post, **data["post_data"])
        author = self.get_or_create(session, models.Author, **data["author_data"])
        post.author = author

        tags = map(lambda tag: self.get_or_create(session, models.Tag, **tag), data["tags_data"])
        for i in tags:
            post.tags.append(i)

        comments = map(lambda comment: self.get_or_create(session, models.Comment, **comment), data["comments_data"])
        for i in comments:
            post.comments.append(i)

        try:
            session.add(post)
            session.commit()
        except sqlalchemy.exc.IntegrityError:
            session.rollback()
        finally:
            session.close()
