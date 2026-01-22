/**
 * SCRIPT PENTRU DEMONSTRAȚIE - Rulează în Browser Console (F12)
 * 
 * Permite "logarea" cu utilizatorii demo pentru prezentare
 */

// Definește utilizatorii demo disponibili
const DEMO_USERS = {
    'demo_action': {
        name: 'Alex - Fan Acțiune',
        genres: ['Action', 'Thriller', 'Adventure'],
        directors: ['Christopher Nolan', 'James Cameron'],
        description: 'Are 3 rating-uri - Hybrid recommendations'
    },
    'demo_scifi': {
        name: 'Maria - Sci-Fi Nerd',
        genres: ['Science Fiction', 'Fantasy'],
        directors: ['Denis Villeneuve', 'Ridley Scott'],
        description: 'Are 3 rating-uri - Hybrid recommendations'
    },
    'demo_drama': {
        name: 'Ion - Drama Lover',
        genres: ['Drama', 'Crime'],
        directors: ['Francis Ford Coppola', 'Martin Scorsese'],
        description: 'Are 3 rating-uri - Hybrid recommendations'
    },
    'demo_cold_start': {
        name: 'Andrei - Cold Start User',
        genres: ['Action', 'Sci-Fi'],
        directors: ['Christopher Nolan'],
        description: '0 rating-uri - Pure Content-Based'
    },
    'demo_heavy': {
        name: 'Mihai - Heavy User',
        genres: ['Action', 'Adventure', 'Sci-Fi', 'Thriller'],
        directors: ['Christopher Nolan', 'Steven Spielberg', 'James Cameron'],
        description: '6+ rating-uri - Strong Collaborative Filtering'
    }
};

// Funcție pentru "logare" cu user demo
async function loginAsDemo(userId) {
    if (!DEMO_USERS[userId]) {
        console.error('❌ User demo invalid!');
        console.log('✅ Utilizatori disponibili:', Object.keys(DEMO_USERS));
        return;
    }
    
    const user = DEMO_USERS[userId];
    
    console.log(`🎭 Logare ca: ${user.name}`);
    console.log(`   Genuri: ${user.genres.join(', ')}`);
    console.log(`   Regizori: ${user.directors.join(', ')}`);
    console.log(`   ${user.description}`);
    
    try {
        const response = await fetch('/api/user/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                demo_user_id: userId,
                preferred_genres: user.genres,
                preferred_directors: user.directors
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            console.log('✅ Logat cu succes!');
            console.log(`   User ID: ${data.user_id}`);
            console.log('🔄 Reîmprospătare pagină...');
            setTimeout(() => location.reload(), 500);
        } else {
            console.error('❌ Eroare:', data);
        }
    } catch (error) {
        console.error('❌ Eroare:', error);
    }
}

// Afișează utilizatori disponibili
function showDemoUsers() {
    console.log('\n🎭 UTILIZATORI DEMO DISPONIBILI:\n');
    Object.entries(DEMO_USERS).forEach(([id, user]) => {
        console.log(`   ${id}`);
        console.log(`   └─ ${user.name}`);
        console.log(`      ${user.description}`);
        console.log('');
    });
    console.log('💡 Folosire: loginAsDemo("demo_action")');
    console.log('💡 SAU: loginAsDemo("demo_cold_start")\n');
}

// Auto-afișare la încărcare
console.log('\n' + '='.repeat(60));
console.log('🎬 SISTEM RECOMANDARE FILME - DEMO MODE');
console.log('='.repeat(60) + '\n');

showDemoUsers();

// Export funcții globale
window.loginAsDemo = loginAsDemo;
window.showDemoUsers = showDemoUsers;
window.DEMO_USERS = DEMO_USERS;
