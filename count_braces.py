with open('static/js/app.js', 'rb') as f:
    content = f.read()

open_brace = content.count(b'{')
close_brace = content.count(b'}')
open_paren = content.count(b'(')
close_paren = content.count(b')')

print(f'{{ : {open_brace}')
print(f'}} : {close_brace}')
print(f'Дисбаланс {{}}: {open_brace - close_brace}')
print()
print(f'( : {open_paren}')
print(f') : {close_paren}')
print(f'Дисбаланс (): {open_paren - close_paren}')
