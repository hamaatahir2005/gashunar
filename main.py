import sys

if __name__ == '__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--self-check':
        from app.selfcheck import run
        raise SystemExit(run(sys.argv[2]))
    from app.bootstrap import run
    raise SystemExit(run())
