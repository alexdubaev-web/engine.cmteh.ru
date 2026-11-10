"""Exercise generated routing rules against a real Apache 2.4 server.

Requires Docker and pulls the official httpd:2.4-alpine image if it is absent.
Run with: python tests/httpd_routing_integration.py
"""
from __future__ import annotations

import http.client
import socket
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlsplit
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from apache_config import config


IMAGE = "httpd:2.4-alpine"


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, text=True, capture_output=True)


def available_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_ready(port: int, container: str) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        state = run("docker", "inspect", "--format", "{{.State.Running}}", container, check=False)
        if state.returncode != 0 or state.stdout.strip() != "true":
            logs = run("docker", "logs", container, check=False).stderr
            raise RuntimeError(f"Apache container exited during startup:\n{logs}")
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=1)
            conn.request("GET", "/")
            response = conn.getresponse()
            response.read()
            if response.status == 200:
                return
        except OSError:
            time.sleep(0.25)
        finally:
            conn.close()
    raise RuntimeError("Apache did not become ready within 30 seconds: " +
                       run("docker", "logs", container, check=False).stderr)


def request(port: int, method: str, target: str, host: str = "engine.cmteh.ru") -> tuple[int, str, bytes]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request(method, target, body=b"payload" if method == "POST" else None, headers={"Host": host})
        response = conn.getresponse()
        body = response.read()
        return response.status, response.getheader("Location", ""), body
    finally:
        conn.close()


def main() -> None:
    run("docker", "image", "inspect", IMAGE, check=False)
    if run("docker", "image", "inspect", IMAGE, check=False).returncode != 0:
        print(f"Pulling official Apache image {IMAGE}...")
        run("docker", "pull", IMAGE)

    with tempfile.TemporaryDirectory(prefix="apache-routing-") as temp:
        root = Path(temp)
        (root / "index.html").write_text("home", encoding="utf-8")
        (root / "index.md").write_text("# home", encoding="utf-8")
        (root / "catalog" / "dz10599").mkdir(parents=True)
        (root / "catalog" / "dz10599" / "index.html").write_text("product", encoding="utf-8")
        (root / "catalog" / "dz10599" / "index.md").write_text("# product", encoding="utf-8")
        (root / "api").mkdir()
        (root / "api" / "orders.php").write_text("api", encoding="utf-8")
        generated = config(True, [{"id": "dz10599"}]).splitlines()
        rewrite_start = generated.index(" RewriteEngine On")
        rewrite_end = generated.index("</IfModule>", rewrite_start)
        mime_start = generated.index("<IfModule mod_mime.c>")
        mime_end = generated.index("</IfModule>", mime_start) + 1
        env_start = generated.index("<IfModule mod_setenvif.c>")
        env_end = generated.index("</IfModule>", env_start) + 1
        headers_start = generated.index("<IfModule mod_headers.c>")
        headers_end = generated.index("</IfModule>", headers_start) + 1
        rules = generated[rewrite_start:rewrite_end] + generated[mime_start:mime_end] + generated[env_start:env_end]
        rules += [line for line in generated[headers_start:headers_end]
                  if "X-Robots-Tag" in line and "seo_markdown" in line]
        (root / ".htaccess").write_text("\n".join(rules), encoding="utf-8")

        apache_conf = '''
ServerRoot "/usr/local/apache2"
PidFile /tmp/httpd.pid
Listen 8080
ServerName engine.cmteh.ru:80
UseCanonicalName On
LoadModule mpm_event_module modules/mod_mpm_event.so
LoadModule authz_core_module modules/mod_authz_core.so
LoadModule authz_host_module modules/mod_authz_host.so
LoadModule unixd_module modules/mod_unixd.so
LoadModule dir_module modules/mod_dir.so
LoadModule mime_module modules/mod_mime.so
LoadModule rewrite_module modules/mod_rewrite.so
LoadModule setenvif_module modules/mod_setenvif.so
LoadModule headers_module modules/mod_headers.so
LoadModule log_config_module modules/mod_log_config.so
TypesConfig conf/mime.types
ErrorLog /proc/self/fd/2
LogLevel rewrite:trace3
CustomLog /proc/self/fd/1 "%r"
DocumentRoot "/usr/local/apache2/htdocs"
AccessFileName .htaccess
<Directory "/usr/local/apache2/htdocs">
    Options FollowSymLinks
    AllowOverride All
    Require all granted
</Directory>
'''
        (root / "httpd.conf").write_text(apache_conf, encoding="utf-8")
        name = f"apache-routing-{next(tempfile._get_candidate_names())}"
        port = available_port()
        try:
            run("docker", "create", "--name", name, "-p", f"127.0.0.1:{port}:8080", IMAGE,
                "httpd-foreground", "-f", "/tmp/httpd.conf")
            run("docker", "cp", str(root / "index.html"), f"{name}:/usr/local/apache2/htdocs/index.html")
            run("docker", "cp", str(root / "index.md"), f"{name}:/usr/local/apache2/htdocs/index.md")
            run("docker", "cp", str(root / ".htaccess"), f"{name}:/usr/local/apache2/htdocs/.htaccess")
            run("docker", "cp", str(root / "catalog"), f"{name}:/usr/local/apache2/htdocs/catalog")
            run("docker", "cp", str(root / "api"), f"{name}:/usr/local/apache2/htdocs/api")
            run("docker", "cp", str(root / "httpd.conf"), f"{name}:/tmp/httpd.conf")
            run("docker", "start", name)
            wait_ready(port, name)

            cases = [
                ("GET", "/catalog//dz10599///?continue=https%3A%2F%2Foutside.example%2Fa%2F%2Fb&token=a%2Fb", 301,
                 "/catalog/dz10599///?continue=https%3A%2F%2Foutside.example%2Fa%2F%2Fb&token=a%2Fb", b""),
                ("GET", "/catalog/%64z10599/", 200, "", b"product"),
                ("GET", "/catalog//%64z10599/?tag=a%2Fb", 301,
                 "/catalog/%64z10599/?tag=a%2Fb", b""),
                ("GET", "/?next=https://outside.example/a//b", 200, "", b"home"),
                ("GET", "/index.md", 200, "", b"# home"),
                ("GET", "/catalog/dz10599/index.md", 200, "", b"# product"),
                ("GET", "/api//orders.php?next=https://outside.example/a//b", 301,
                 "/api/orders.php?next=https://outside.example/a//b", b""),
                ("POST", "/api//orders.php", 200, "", b"api"),
                ("GET", "/////", 301, "/", b""),
            ]
            for method, target, expected_status, expected_location, expected_body in cases:
                status, location, body = request(port, method, target)
                assert status == expected_status, (method, target, status, location,
                    run("docker", "logs", name, check=False).stdout + run("docker", "logs", name, check=False).stderr,
                    run("docker", "exec", name, "ls", "-la", "/usr/local/apache2/htdocs", check=False).stdout)
                if location:
                    parsed_location = urlsplit(location)
                    assert parsed_location.hostname == "engine.cmteh.ru", (method, target, location)
                    assert parsed_location.path + ("?" + parsed_location.query if parsed_location.query else "") == expected_location, (method, target, location)
                else:
                    assert expected_location == "", (method, target, location)
                if expected_body:
                    assert expected_body in body, (method, target, body)
                print(f"PASS {method} {target} -> {status}" + (f" {location}" if location else ""))

            for target in ("/index.md", "/catalog/dz10599/index.md"):
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                try:
                    conn.request("GET", target, headers={"Host": "engine.cmteh.ru"})
                    response = conn.getresponse();response.read()
                    assert response.getheader("Content-Type") == "text/markdown; charset=utf-8", (target, response.getheader("Content-Type"))
                    assert response.getheader("X-Robots-Tag") == "noindex, follow", (target, response.getheader("X-Robots-Tag"))
                finally:
                    conn.close()
                print(f"PASS Markdown headers {target}")

            for target, canonical, content in (
                ("/////", "/", b"home"),
                ("/catalog//dz10599///?continue=https%3A%2F%2Foutside.example%2Fa%2F%2Fb&token=a%2Fb",
                 "/catalog/dz10599/?continue=https%3A%2F%2Foutside.example%2Fa%2F%2Fb&token=a%2Fb", b"product"),
                ("/catalog//%64z10599/?tag=a%2Fb", "/catalog/%64z10599/?tag=a%2Fb", b"product"),
                ("/api//orders.php?next=https://outside.example/a//b",
                 "/api/orders.php?next=https://outside.example/a//b", b"api"),
            ):
                status, location, _ = request(port, "GET", target)
                assert status == 301
                hops = 1
                while True:
                    parsed = urlsplit(location)
                    assert parsed.scheme == "http" and parsed.hostname == "engine.cmteh.ru", (target, location)
                    target_path = parsed.path + ("?" + parsed.query if parsed.query else "")
                    status, next_location, body = request(port, "GET", target_path)
                    if status != 301:
                        break
                    location = next_location
                    hops += 1
                    assert hops <= 10, (target, location)
                assert status == 200 and content in body, (target, status, body)
                assert parsed.path + ("?" + parsed.query if parsed.query else "") == canonical
                print(f"PASS canonical {target} -> {hops} redirect(s) -> {canonical}")

            status, location, _ = request(port, "GET", "//evil.example/path")
            parsed_location = urlsplit(location)
            assert status == 301 and parsed_location.hostname == "engine.cmteh.ru", (status, location)
            assert parsed_location.path == "/evil.example/path", (status, location)
            print(f"PASS scheme-relative-looking path stays on canonical host: {location}")
        finally:
            run("docker", "rm", "-f", name, check=False)


if __name__ == "__main__":
    main()
