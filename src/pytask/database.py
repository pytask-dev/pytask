from pony import orm


db = orm.Database()


class State(db.Entity):
    task = orm.Required(str)
    node = orm.Required(str)
    state = orm.Required(str)

    orm.PrimaryKey(task, node)


def create_database(provider, filename, create_db, create_tables):
    try:
        db.bind(provider=provider, filename=filename, create_db=create_db)
        db.generate_mapping(create_tables=create_tables)
    except orm.BindingError:
        pass


@orm.db_session
def create_or_update_state(first_key, second_key, state):
    try:
        state_in_db = State[first_key, second_key]
    except orm.ObjectNotFound:
        State(task=first_key, node=second_key, state=state)
    else:
        state_in_db.state = state
