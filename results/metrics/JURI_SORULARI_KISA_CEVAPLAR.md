# Jüri Sorularına Kısa Cevaplar

## Neden en yüksek doğruluk veren eski modeli değil de yeni modeli seçtiniz?
Çünkü eski model kendi test dağılımında daha yüksek görünse de dış testte yalnızca %52.74 doğruluk ve %6.04 fake recall verdi. Yeni model ise orijinal testte hâlâ %99.10 seviyesinde kalırken dış testte %92.15 doğruluğa ulaştı. Nihai sistem için genelleme daha önemliydi.

## Yeni model neden orijinal testte biraz düştü?
Çünkü daha çeşitli veri gördü ve yalnızca ilk veri setine aşırı uyum sağlamak yerine daha genel sahtecilik izlerini öğrenmeye başladı. Bu küçük kayıp, dış testteki büyük kazanım karşılığında kabul edilebilir.

## Neden sadece görüntü, neden video değil?
Bu proje görüntü tabanlı deepfake tespitine odaklandı. Video tabanlı yöntemler zamansal ipuçlarından yararlanabilir; bu da gelecek çalışma başlığıdır.

## Face crop neden kullanıldı?
Canlı internet görsellerinde modele yüz bölgesini daha tutarlı vermek için. Ancak bağlamsal ipuçlarını kaybetme riski olduğu için ileride tam görüntü + geniş crop + sıkı crop yaklaşımı denenebilir.

## Projenin en önemli bulgusu nedir?
Aynı dağılımdaki yüksek skorların tek başına güvenilir olmadığını; veri çeşitliliğinin dağılım dışı genelleme için kritik olduğunu göstermesidir.
