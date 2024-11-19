// Sayfa yüklendikten sonra çalışacak bir fonksiyon
document.addEventListener("DOMContentLoaded", function() {
    // Kayıt formunu kontrol etme işlemleri için bir örnek
    const signupForm = document.querySelector("form");

    signupForm.addEventListener("submit", function(event) {
        // Kullanıcı adı, şifre, GitHub adı ve CV kontrolü
        const username = document.getElementById("username").value;
        const password = document.getElementById("password").value;
        const github = document.getElementById("github").value;
        const cv = document.getElementById("cv").files.length;

        // Formu doğrulama
        if (!username || !password || !github || cv === 0) {
            alert("Tüm alanlar doldurulmalıdır ve CV dosyası yüklenmelidir.");
            event.preventDefault(); // Formun gönderilmesini engeller
        }
    });
});
