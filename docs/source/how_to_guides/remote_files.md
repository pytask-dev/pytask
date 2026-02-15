# Remote files

So far, we have only dealt with local files in the tutorials and guides. But there are
lots of use cases to deal with remote files.

- You distribute the workflow without the data and want to make it easy for others to
    get started. So, some tasks reference remote files instead of local files.
- You store the workflow results in remote storage to save and distribute them.

pytask uses [universal-pathlib](https://github.com/fsspec/universal_pathlib) to work
with remote files. The package provides a `pathlib`-like interface, making it very easy
to interact with files from an HTTP(S)-, Dropbox-, S3-, GCP-, Azure-based filesystem,
and many more.

## HTTP(S)-based filesystem

As an example for dealing with an HTTP(S)-based filesystem, we will download the iris
data set and save it as a CSV file.

```py
--8<-- "docs_src/how_to_guides/remote_files/https.py"
```

## Other filesystems

universal_pathlib supports Azure Storage, Dropbox, Google Cloud Storage, AWS S3, and
[many more filesystems](https://github.com/fsspec/universal_pathlib#currently-supported-filesystems-and-schemes).

For example, let us try accessing a file in an S3 bucket. We pass `anon=True` to
`upath.UPath` since no credentials are required.

```pycon
>>> from upath import UPath
>>> path = UPath("s3://upath-aws-example/iris.data", anon=True)
>>> path.stat()
ModuleNotFoundError
...
ImportError: Install s3fs to access S3
```

Some filesystems are supported
[out-of-the-box](https://filesystem-spec.readthedocs.io/en/latest/api.html#built-in-implementations).
[Others](https://filesystem-spec.readthedocs.io/en/latest/api.html#other-known-implementations)
are available as [plugins](../glossary.md#plugin) and require additional packages.

After installing s3fs, rerun the command.

```pycon
>>> path.stat()
{'ETag': '"42615765a885ddf54427f12c34a0a070"',
 'LastModified': datetime.datetime(2023, 12, 11, 23, 50, 3, tzinfo=tzutc()),
 'size': 4551,
 'name': 'upath-aws-example/iris.data',
 'type': 'file',
 'StorageClass': 'STANDARD',
 'VersionId': None,
 'ContentType': 'binary/octet-stream'}
```

Usually, you will need credentials to access files. Search in
[fsspec's documentation](https://filesystem-spec.readthedocs.io/en/latest) or the
plugin's documentation, here [s3fs](https://s3fs.readthedocs.io/en/latest/#credentials),
for information on authentication. One way would be to set the environment variables
`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`.

## Detecting changes in remote files

pytask uses the [entity tag (ETag)](https://en.wikipedia.org/wiki/HTTP_ETag) to detect
changes in remote files. The ETag is an optional header field that can signal a file has
changed. For example,
[AWS S3 uses an MD5 digest](https://teppen.io/2018/06/23/aws_s3_etags/) of the uploaded
file as the ETag. If the file changes, so does the ETag, and pytask will detect it.

Many files on the web do not provide an ETag like this version of the iris dataset.

```pycon
>>> import httpx
>>> url = "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
>>> r = httpx.head(url)
>>> r.headers
{'Server': 'nginx/1.25.3', 'Date': 'Sun, 10 Dec 2023 23:59:21 GMT', 'Connection': 'keep-alive'}
```

In these instances, pytask does not recognize if the file has changed. If you want to
force rerunning the task, delete a product of the task.
