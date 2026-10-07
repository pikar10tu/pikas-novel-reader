import urllib.request

headers = {'User-Agent': 'Mozilla/5.0'}

# 1. Download Dragon original cover
try:
    url1 = 'https://i0.wp.com/etherreads.com/wp-content/uploads/2024/01/04c14e7a-5278-4546-8ca5-2b26c09a7a32.jpg'
    req1 = urllib.request.Request(url1, headers=headers)
    with open('covers/dragon_orig.jpg', 'wb') as f:
        f.write(urllib.request.urlopen(req1, timeout=10).read())
    print("Downloaded dragon_orig.jpg")
except Exception as e:
    print("Error dragon orig:", e)

# 2. Download Suicide hunter original cover
try:
    url2 = 'https://noveltranslationhub.com/wp-content/uploads/2024/01/sss-class-suicide-hunter-193x278-1.png'
    req2 = urllib.request.Request(url2, headers=headers)
    with open('covers/hunter_orig.png', 'wb') as f:
        f.write(urllib.request.urlopen(req2, timeout=10).read())
    print("Downloaded hunter_orig.png")
except Exception as e:
    print("Error hunter orig:", e)
