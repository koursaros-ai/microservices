import click
# from utils.train.roberta_inference import RobertaInference
import os
# from koursaros.utils.database.psql import Conn

@click.command()
@click.option('-tr', '--train', multiple=True)
@click.option('-te', '--test', nargs=1)
@click.option('-n', '--name', nargs=1)
@click.option('-a', '--arch', nargs=1)
@click.option('-o', '--output_bucket', nargs=1)
@click.option('-db', '--database', nargs=1)
@click.option('-e', '--epochs', nargs=1, default=1)
@click.option('-c', '--checkpoint', nargs=1)
@click.option('-u', '--upload_only', is_flag=True)
@click.option('-r', '--regression', is_flag=True)
@click.argument('labels', nargs=-1)
@click.pass_obj
def train(*args):
    """Save current directory's pipeline"""
    main(*args)

def main(path_manager,
          train,
          test,
          name,
          arch,
          output_bucket,
          database,
          epochs,
          checkpoint,
          upload_only,
          regression,
          labels):
    main()
    # if arch == 'roberta_inference':
    #     assert regression or labels is not None or upload_only
    #     model = RobertaInference(name, labels=labels, regression=regression)
    # else:
    #     raise NotImplementedError()
    # if not upload_only:
    #     if database is not None:
    #         p = Conn(
    #             host=HOST,
    #             user=USER,
    #             password=PASS,
    #             dbname=args.dbname,
    #             sslmode=SSLMODE,
    #             cert_path=CERT_PATH
    #         )
    #         query_fn = p.query
    #         train, test = model.get_data(args.train, args.test, from_db=args.db, query_fn=query_fn)
    #     else:
    #         train, test = model.get_data(args.train, args.test)
    #     model.train(train, test, args.checkpoint)
    # model.save_model(args.output_bucket)
