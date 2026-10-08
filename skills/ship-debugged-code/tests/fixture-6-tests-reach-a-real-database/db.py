import settings

open("CONNECTED.marker", "w").write(settings.DATABASE_URL)


def execute(sql, params=()):
    raise RuntimeError("no database in this fixture")


def scalar(sql):
    raise RuntimeError("no database in this fixture")
