"""Apache 2.4 static/PHP hosting configuration, generated for the chosen mode."""
import re

def config(indexable,products):
 lines=['Options -Indexes','DirectoryIndex index.html','ErrorDocument 404 /404/','<IfModule mod_rewrite.c>',' RewriteEngine On',' RewriteCond %{ENV:REDIRECT_STATUS} ^$',' RewriteCond %{THE_REQUEST} \\s/+404(?:/index\\.html|/?)(?:[?\\s]) [NC]',' RewriteRule ^404(?:/index\\.html|/?)$ - [R=404,L]']
 for p in products:
  slug=p['id'];pattern=re.escape(slug)
  lines += [' RewriteCond %{REQUEST_URI} !^/catalog/'+pattern+'/$', ' RewriteRule ^catalog/'+pattern+'(?:/index\\.html|/?)$ /catalog/'+slug+'/ [R=301,L,NC]']
 lines += [' RewriteCond %{THE_REQUEST} \\s/+(.*/)?index\\.html(?:[?\\s]) [NC]',' RewriteRule ^(.*)index\\.html$ /$1 [R=301,L,NE]','</IfModule>',
 '<IfModule mod_setenvif.c>', ' SetEnvIfExpr "%{QUERY_STRING} =~ /(^|&)(q|search|sort|brand|filter|page|category)=/" seo_search', ' SetEnvIf Request_URI "^/(privacy|consent|404)/" seo_utility','</IfModule>',
 '<IfModule mod_headers.c>',
 ' Header always set X-Content-Type-Options "nosniff"',' Header always set Referrer-Policy "strict-origin-when-cross-origin"',' Header always set X-Frame-Options "SAMEORIGIN"',' Header always set Permissions-Policy "camera=(), microphone=(), geolocation=()"',
 ' Header always set Content-Security-Policy "default-src \'self\'; script-src \'self\' https://mc.yandex.ru https://yastatic.net; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data: https://mc.yandex.ru https://mc.yandex.com https://yastatic.net; font-src \'self\'; connect-src \'self\' https://mc.yandex.ru https://mc.yandex.com https://yastatic.net wss://mc.yandex.ru; frame-src \'self\' https://metrika.yandex.ru blob:; child-src \'self\' blob:; form-action \'self\'; base-uri \'self\'; frame-ancestors \'self\'"']
 if indexable:lines+=[' Header always set X-Robots-Tag "noindex, follow" env=seo_search',' Header always set X-Robots-Tag "noindex, follow" env=seo_utility']
 else:lines+=[' Header always set X-Robots-Tag "noindex, nofollow"']
 lines+=['</IfModule>','<IfModule mod_deflate.c>',' AddOutputFilterByType DEFLATE text/html text/plain text/css application/javascript application/json application/xml text/xml image/svg+xml','</IfModule>',
 '<IfModule mod_expires.c>',' ExpiresActive On',' ExpiresByType text/css "access plus 1 year"',' ExpiresByType application/javascript "access plus 1 year"',' ExpiresByType font/woff2 "access plus 1 year"',' ExpiresByType image/webp "access plus 1 day"',' ExpiresByType image/jpeg "access plus 1 day"','</IfModule>',
 '<FilesMatch "^(\\.|.*\\.(sql|sqlite|log|bak|env|zip|tar|gz)$)">',' Require all denied','</FilesMatch>']
 return '\n'.join(lines)+'\n'
