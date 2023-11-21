from pwn import *
from typing import Optional
import gamelib
import random
import time
import re

# wrapper function for sending
# exists to ease potential migration to obfuscated connection
def send_to_service(conn, data):
    conn.sendline(data)


# wrapper function for receiving 
# exists to ease potential migration to obfuscated connection
def recv_until_from_service(conn, until):
    try:
        data = conn.recvuntil(until)
    except EOFError:
        raise gamelib.MumbleException(f"Connection closed unexpectedly while waiting for {until}")
    if data == "":
        raise gamelib.MumbleException("Response was empty")
    return data


# wrapper function for receiving 
# exists to ease potential migration to obfuscated connection
def recv_line_from_service(conn):
    try:
        data = conn.recvline()
    except EOFError:
        raise gamelib.MumbleException("Connection closed unexpectedly")
    if data == "":
        raise gamelib.MumbleException("Response was empty")
    return data


# register a new user and login
def register_and_login(conn):
    # the initial welcome screen
    recv_until_from_service(conn, "Goodbye\n")
    send_to_service(conn, "Register")
    recv_until_from_service(conn, "First name?\n")
    first_name, last_name = gen_german_name()
    password = gamelib.usernames.generate_password(min_length=24, max_length=28)
    send_to_service(conn, first_name)
    recv_until_from_service(conn, "Last name?\n")
    send_to_service(conn, last_name)
    recv_until_from_service(conn, "Password?\n")
    send_to_service(conn, password)
    print(f"Trying to register {first_name} {last_name} {password}")
    recv_until_from_service(conn, f"Welcome, {first_name}\n")
    return (first_name, last_name, password)


# register a new user and login
def register_and_login_specific(conn, name):
    # the initial welcome screen
    recv_until_from_service(conn, "Goodbye\n")
    send_to_service(conn, "Register")
    recv_until_from_service(conn, "First name?\n")
    _, last_name = gen_german_name()
    password = gamelib.usernames.generate_password(min_length=24, max_length=28)
    send_to_service(conn, name)
    recv_until_from_service(conn, "Last name?\n")
    send_to_service(conn, last_name)
    recv_until_from_service(conn, "Password?\n")
    send_to_service(conn, password)
    print(f"Trying to register {name} {last_name} {password}")
    recv_until_from_service(conn, f"Welcome, {name}\n")
    return (name, last_name, password)


# login existing user 
def login(conn, first_name, last_name, password):
    # the initial welcome screen
    recv_until_from_service(conn, "Goodbye\n")
    send_to_service(conn, "Login")
    recv_until_from_service(conn, "First name?\n")
    send_to_service(conn, first_name)
    recv_until_from_service(conn, "Last name?\n")
    send_to_service(conn, last_name)
    recv_until_from_service(conn, "Password?\n")
    send_to_service(conn, password)
    recv_until_from_service(conn, f"Welcome, {first_name}\n")

def get_employee_id(conn, first: str, last: str) -> Optional[str]:
    send_to_service(conn, b"View the employee register")
    employee_list = recv_until_from_service(conn, b"End of employee list.\n").decode()
    for line in employee_list.splitlines():
        rx = re.match(r"^(?P<eid>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}) \| .* \| (?P<first>.*) \| (?P<last>.*)$", line)
        if rx is not None and rx.group("first") == first and rx.group("last") == last:
            return rx.group("eid")
    return None

# receive the main menu
def receive_main_menu(conn):
    recv_until_from_service(conn,
        b'What do you want to do?\n'
        b'Check my tasks\n'
        b'Check my holidays\n'
        b'Encrypt or decrypt a message\n'
        b'Read or post important announcements\n'
        b'View the employee register\n'
    )


# task menu recv blob
def enter_task_menu(conn):
    send_to_service(conn, "Check my tasks")
    recv_until_from_service(conn,
        b'Create task\n'
        b'Complete task\n'
        b'List all tasks\n'
    )


# create a task
def create_task(conn, task_name=None, description=None):
    send_to_service(conn, "Create task")
    if not task_name:
        task_name = gamelib.usernames.generate_random_string(l=20)
    if not description:
        description = gamelib.usernames.generate_random_string(l=20)
    steps = gamelib.usernames.generate_username() + ", " + gamelib.usernames.generate_username() + " and " + gamelib.usernames.generate_username()
    epic = gamelib.usernames.generate_name(words = 5, sep = " ")
    sprint = gamelib.usernames.generate_name(words = 3, sep = " ")
    workhours = random.randint(2,72)
    recv_until_from_service(conn, "Task name?\n")
    send_to_service(conn, task_name)
    recv_until_from_service(conn, "Description?\n")
    send_to_service(conn, description)
    recv_until_from_service(conn, "Steps to fulfill the task?\n")
    send_to_service(conn, steps)
    recv_until_from_service(conn, "Which epic does this task belong to?\n")
    send_to_service(conn, epic)
    recv_until_from_service(conn, "Which sprint do you want to work on this?\n")
    send_to_service(conn, sprint)
    recv_until_from_service(conn, "How many workhours do you think this takes?\n")
    send_to_service(conn, str(workhours))
    answer = recv_line_from_service(conn)
    return (answer, task_name, description, steps, epic, sprint, workhours)


# complete a task
def complete_task(conn, task_name, task_epic):
    send_to_service(conn, "Complete task")
    recv_until_from_service(conn, "Task name?\n")
    send_to_service(conn, task_name)
    recv_until_from_service(conn, "Task epic?\n")
    send_to_service(conn, task_epic)
    answer = recv_line_from_service(conn)
    return answer


# check details of a task
def check_task_details(conn):
    send_to_service(conn, "list all tasks")
    # Success
    line = recv_line_from_service(conn)
    print(f"received {line} as first response")
    answer = recv_until_from_service(conn, b"\n\n")
    return answer


# holiday menu recv blob
def enter_holiday_menu(conn):
    send_to_service(conn, "Check my holidays")
    recv_until_from_service(conn,
        b'Take time off\n'
        b'Cancel holiday\n'
        b'Check current bookings\n'
    )


def take_time_off(conn):
    send_to_service(conn, "Take time off")
    month = random.randint(1,12)
    rand1 = random.randint(1,10)
    rand2 = random.randint(1,10)
    big = max(rand1,rand2)
    small = min(rand1,rand2)
    start_date = str(small) + "-" + str(month) + "-24" 
    end_date = str(big) + "-" + str(month) + "-24"
    reason = gamelib.usernames.generate_username() 
    destination = gamelib.usernames.generate_username() 
    phone = ""
    for i in range(0,random.randint(12,16)):
        phone += str(random.randint(0,9))
    recv_until_from_service(conn, "Start date?\n")
    send_to_service(conn, start_date)
    recv_until_from_service(conn, "End date?\n")
    send_to_service(conn, end_date)
    recv_until_from_service(conn, "Why do you want to take holiday?\n")
    send_to_service(conn, reason)
    recv_until_from_service(conn, "Where will you go?\n")
    send_to_service(conn, destination)
    recv_until_from_service(conn, "How can we reach you during your holiday? Please enter your phone number:\n")
    send_to_service(conn, phone)
    answer = recv_line_from_service(conn)
    return (answer, start_date, end_date, reason, destination, phone)


def cancel_holiday(conn, start_date, end_date):
    send_to_service(conn, "Cancel holiday")
    recv_until_from_service(conn, "Start date?\n")
    send_to_service(conn, start_date)
    recv_until_from_service(conn, "End date?\n")
    send_to_service(conn, end_date)
    answer = recv_line_from_service(conn)
    return answer


# the only way to know I got all the bookings is also consuming the general menu here
def check_current_bookings(conn):
    send_to_service(conn, "Check current bookings")
    answer = recv_until_from_service(conn, "employee register\n")
    return answer


def mc_enter_menu(conn):
    send_to_service(conn, b'Encrypt or decrypt a message')
    recv_until_from_service(conn,
        b'Encrypt a message to someone else\n'
        b'Decrypt a message I received\n'
    )

def mc_encrypt_message(conn, eid: str, message_b64s: str) -> str:
    send_to_service(conn, b"Encrypt a message to someone else")
    recv_until_from_service(conn, b"Recipient's employee ID?\n")
    send_to_service(conn, eid.encode())
    recv_until_from_service(conn, b"Message Body? (up to 512 bytes, base64)\n")
    send_to_service(conn, message_b64s.encode())
    recv_until_from_service(conn, b"This is your encrypted message:\n")
    return recv_line_from_service(conn).decode()

def mc_decrypt_message(conn, ciphertext_b64s: str) -> bytes:
    send_to_service(conn, b"Decrypt a message I received")
    recv_until_from_service(conn, b"Ciphertext? (up to 512 bytes, base64)\n")
    send_to_service(conn, ciphertext_b64s.encode())
    recv_until_from_service(conn, b"This is your decrypted message:\n")
    return recv_line_from_service(conn)

def board_enter_menu(conn):
    send_to_service(conn, b'Read or post important announcements')
    recv_until_from_service(conn,
        b'Get number of active announcements\n'
        b'Get announcement by ID\n'
        b'Get announcement by number\n'
        b'Post an announcement\n'
    )

def board_get_count(conn) -> int:
    send_to_service(conn, b"Get number of active announcements")
    response = recv_line_from_service(conn).decode()
    rx = re.match(r"^Number of announcements: (?P<count>\d+)$", response)
    if rx:
        return int(rx.group("count"))
    raise gamelib.MumbleException("Board did not return number of messages.")

def _extract_from_announcement(announcement: str) -> dict[str, str]:
    rx = re.match(
        r"^ANNOUNCEMENT\. ATTENTION PLEASE, THIS IS "
        r"(?P<first>[^ \-]+?[ \-][^ ]+ [^ ]+) (?P<last>[^ ]*?) "
        r"SPEAKING TO EVERYONE\. (?P<message1>.*?) I REPEAT\. "
        r"(?P<message2>.*?) END OF ANNOUNCEMENT\.",
        announcement
    )
    if not rx or rx.group("message1") != rx.group("message2"):
        raise gamelib.MumbleException("Gateway formatted announcement in a wrong way.")
    return {
        "first": rx.group("first"),
        "last": rx.group("last"),
        "message": rx.group("message1")
    }

def board_get_message_by_id(conn, message_id: str) -> dict[str, str]:
    send_to_service(conn, b"Get announcement by ID")
    recv_until_from_service(conn, b"Message ID?\n")
    send_to_service(conn, message_id.encode())
    response = recv_line_from_service(conn)
    return _extract_from_announcement(response.decode())

def board_get_message_by_number(conn, message_number: int) -> dict[str, str]:
    send_to_service(conn, b"Get announcement by number")
    recv_until_from_service(conn, b"Message Number?\n")
    send_to_service(conn, str(message_number).encode())
    response = recv_line_from_service(conn)
    return _extract_from_announcement(response.decode())

def board_put(conn, message: str) -> str:
    send_to_service(conn, b"Post an announcement")
    recv_until_from_service(conn, b"Text? (up to 1000 characters)\n")
    send_to_service(conn, message.encode())
    recv_until_from_service(conn, b"Your important announcement has been filed under the ID ")
    message_id = recv_line_from_service(conn)[:-2]
    return message_id.decode()

##### TEST MESSAGES ######

TEST_MESSAGES = [
    "Announcement: If your coffee machine is not working today, complaining about it won't fix it; Let's focus on bug fixes instead!",
    "PSA: The mute button exists for a reason; Let's use it during calls, especially if you're multitasking with a blender orchestra in the background;",
    "Friendly reminder: Your keyboard is not a drum set; Let's keep the noise pollution down during meetings;",
    "Announcement: The deadline for submitting your cat memes to the #PetPics channel is extended; Let's flood it with furry joy!",
    "Team, the 'reply all' button is not a toy; Use it responsibly, unless you want your cat meme to become a company-wide sensation;",
    "To our data center contractors: The server room is not a nap room; Please resist the temptation to cozy up with your laptop in there;",
    "Announcement: Use emojis wisely; A single thumbs up suffices we don't need a whole emoji novel for each message;",
    "Reminder: The dress code is not optional; Yes, that includes pants;",
    "Announcement: The 'reply with GIF' feature is not an excuse to communicate exclusively in animated images; Words are still a thing;",
    "Friendly reminder: The 'mic off' button is like a superhero's cloak; Use it wisely and save us from unexpected background noise villains;",
    "Team, our virtual office doesn't have walls, but it does have etiquette; Let's build a culture where everyone feels heard and respected;",
    "Announcement: We're all in this together, so let's lift each other up, not tear each other down; Positive vibes only, please!",
    "Quick poll: Who's up for a virtual happy hour this Friday? BYOB Bring Your Own Beverage and non-toxic conversation topics!",
    "Important notice: If your internet connection is having a bad day, don't take it out on your keyboard; Deep breaths and restarts work wonders;",
    "Heads up! The 'urgent' flag is not a decoration; Reserve it for actual emergencies, like running out of coffee filters;",
    "Announcement: Constructive criticism is welcome; destructive criticism is not; Let's build each other up, not break each other down;",
    "Reminder: The #Caturday channel is for cats, not political debates; Let's keep it fluffy and drama-free;",
    "Attention team: A friendly reminder to stretch and take breaks; Burnout is not a badge of honor;",
    "Announcement: The 'urgent' flag is not a magic wand; Using it won't make your request magically more important; Let's be mindful of priorities;",
    "PSA: Your video background says a lot about you; Let's aim for professional, not a chaotic collection of questionable life choices;",
    "Team, the #TechTalk channel is for tech discussions, not debates on the best pizza toppings; Let's stay on topic, even if pineapple is involved;",
    "Quick reminder: The 'send' button is not a time machine; Double-check before launching that message into the digital abyss;",
    "Attention: The #Random channel is not a therapy session; Let's keep it lighthearted and random, not deep and existential;",
    "Friendly reminder: The 'Caps Lock' key is not a volume control for emphasis; Let's keep the shouting to a minimum;",
    "Team, let's practice the art of the timely response; Ghosting is for Halloween, not professional communication;",
    "Reminder: The #TechSupport channel is for tech issues, not conspiracy theories; Let's save those for after hours;",
    "Important notice: Meetings are not an excuse to multitask; Your cat's antics can wait; let's focus on the agenda;",
    "PSA: The 'mark as unread' button is not a to-do list; Let's be honest about our unread messages and tackle them head-on;",
    "Announcement: The company-wide spreadsheet is not a canvas for your artistic expressions; Let's keep it data-driven and professional;",
    "Friendly reminder: The #Jokes channel is for jokes, not passive-aggressive jabs; Let's keep the laughter genuine;",
    "Quick poll: Who prefers virtual fist bumps over awkward handshakes? Let's gauge our collective preference;",
    "Attention team: The 'do not disturb' status is not an invitation to bombard someone with messages; Respect the virtual space;",
    "Team, the virtual suggestion box is open; Share your ideas for improving our virtual workspace; Let's make it a better place for everyone!",
    "Reminder: The #DIY channel is for DIY projects, not DIY therapy sessions; Let's keep it creative and constructive;",
    "Heads up! The 'read receipts' feature is mandatory; Do not hide in mystery;",
    "PSA: The #FitnessChallenge is a friendly competition, not an excuse to Photoshop yourself into an Olympic athlete; Keep it real, folks!",
    "Attention Team: Just a gentle reminder that the mute button works wonders during meetings; No need to share your keyboard symphonies with the entire company;",
    "Heads up, folks! The company-provided coffee machines are on a temporary vacation, but let's try to resist the urge to turn the #General channel into a complaint hotline;",
    "Announcement: In case you missed it, the 'reply all' button is not a showcase for your one-person comedy show; Keep it professional, please;",
    "PSA: The #PetPics channel is for actual pets, not stock photos claiming to be your furry friend; Let's keep it authentic, shall we?",
    "Friendly reminder: The 'urgent' flag is for urgent matters; Let's not dilute its importance with every minor request;",
    "Announcement: Just a heads up that the dress code policy extends to the virtual realm; Yes, even on casual Fridays;",
    "Team, a quick note on the #Caturday channel: While cats are delightful, let's not turn it into a feline philosophy debate;",
    "Data center employees: The server room is not a cozy nook for impromptu napping sessions; Save it for your actual bed;",
    "Attention: The 'mic off' button is not a decorative element; Feel free to use it during meetings to spare us from background noise operas;",
    "Heads up! The #Random channel is for randomness, not a dumping ground for your unresolved existential crises; Keep it lighthearted, please;",
    "Announcement: While the #Jokes channel welcomes humor, let's avoid jokes that double as subtle insults; Comedy, not passive aggression;",
    "Quick poll: Who thinks the virtual office would be a more peaceful place if we used the 'mark as read' button responsibly? Thoughts?",
    "Important notice: The 'Caps Lock' key is not a substitute for well-thought-out arguments; Let's express ourselves without resorting to virtual shouting matches;",
    "Team, just a gentle suggestion: If your internet connection has a bad day, maybe save the frustration for your provider, not your keyboard;",
    "Announcement: The #TechTalk channel is for tech discussions, not for proving your conspiracy theories; Let's stick to facts, not fiction;",
    "Friendly reminder: The 'send' button doesn't have a memory erase feature; Double-check your messages before they become permanent;",
    "PSA: The #DIY channel is for creative DIY projects, not DIY therapy sessions; Let's save the deep life reflections for our personal journals;",
    "Announcement: The virtual suggestion box is open, but let's focus on constructive ideas; It's not a place for passive-aggressive venting;",
    "Team, we've noticed a decline in meeting punctuality; Time is a valuable resource for all of us; Let's make a collective effort to start and end on time;",
    "Announcement: It has come to our attention that the level of detail in some project reports is lacking; Let's aim for thoroughness and accuracy moving forward;",
    "Attention: The recent increase in extended breaks is affecting overall productivity; Let's all be mindful of our time management and adhere to the agreed-upon break durations;",
    "Announcement: The tone in certain communication channels has been less than professional; Let's maintain a respectful and business-appropriate language to foster a positive virtual environment;",
    "Quick reminder: The #Feedback channel is for constructive feedback, not a platform for personal grievances; Let's address concerns through proper channels for resolution;",
    "Team, we've noticed a trend of missed deadlines; Accountability is crucial for our success; Let's ensure we're meeting our commitments and delivering on time;",
    "Announcement: Quality control is a priority; Let's review our work thoroughly before submission to avoid errors and uphold the high standards we strive for;",
    "Attention: It's essential to maintain professionalism during virtual meetings; Side conversations and distractions are disruptive; Let's give our full attention to the agenda at hand;",
    "Announcement: The #Ideas channel is for innovative suggestions, not a platform for sarcasm; Let's encourage a culture of constructive and positive contributions;",
    "Reminder: The company resources are to be used responsibly; Unauthorized software installations can compromise security; Let's adhere to IT policies to safeguard our digital environment;",
    "Team, the level of collaboration in cross-functional projects has room for improvement; Let's enhance communication for better synergy;",
    "Announcement: The use of acronyms and industry jargon can be alienating to some team members; Let's strive for clear communication that everyone can understand;",
    "Attention: The recent surge in multitasking during meetings is affecting our ability to make informed decisions; Let's be present and engaged to maximize efficiency;",
    "Announcement: The #InnovationChallenge is an opportunity for creative solutions, not a competition for who can push the boundaries the furthest; Let's keep it focused on practical innovation;",
    "Quick reminder: The company-wide calendar is a valuable tool; Let's utilize it for scheduling to avoid conflicts and ensure everyone is on the same page;",
    "Team, the #Collaboration channel is for project updates, not personal anecdotes; Let's streamline communication to maintain a professional environment;",
    "Announcement: The recent trend of extended response times in the #UrgentMatters channel is concerning; Let's prioritize timely responses to urgent matters for swift problem resolution;",
    "Attention: The #ClientInteractions channel is for client-related discussions, not a platform for airing grievances about client expectations; Let's address concerns constructively;",
    "Announcement: The virtual office space reflects our professionalism; Let's ensure our backgrounds and appearances during video calls maintain a high standard;",
    "Reminder: The #WellnessWednesday initiative is for promoting well-being, not a platform for oversharing personal health details; Let's keep it supportive and respectful;",
    "Team, the #TrainingResources channel is for sharing educational content, not a repository for outdated materials; Let's keep it current to support ongoing learning;",
    "Announcement: The recent uptick in off-topic discussions during project-specific channels is diverting focus; Let's use channels purposefully to maintain efficiency;",
    "Attention: The #Recognition channel is for acknowledging achievements, not a platform for subtle self-promotion; Let's celebrate each other's successes humbly;",
    "Announcement: The recurring issue of missed sprint goals is impacting our project timelines; Let's reassess and commit to realistic and achievable targets;",
    "Quick reminder: The #ProductivityTips channel is for sharing efficiency hacks, not for debating the merits of time management philosophies; Let's keep it practical;",
    "Team, the #ClientFeedback channel is for constructive input, not a forum for challenging client decisions; Let's approach feedback professionally and diplomatically;",
    "Announcement: The recent influx of personal anecdotes in the #MondayMotivation channel is diluting its purpose; Let's keep it focused on motivating content for the week ahead;",
    "Attention: The #TechUpdates channel is for critical technology updates, not a space for personal tech grievances; Let's maintain a professional tone in our discussions;",
    "Announcement: The recent deviation from the company branding guidelines in internal presentations is noted; Let's adhere to the guidelines to maintain a consistent image;",
    "Reminder: The #TaskDelegation channel is for assigning and discussing tasks, not a platform for questioning leadership decisions; Let's trust the process and move forward collaboratively;",
]

##### NAME GENERATOR #####

FIRST_NAMES = {
    "male": [
        "Adalbald", "Albert", "Alfons", "Almar", "Anno", "Anton",
        "Archibald", "Arthur", "Artur", "Arwin", "August", "Benedikt",
        "Benno", "Berwin", "Bruno", "Carsten", "Clemens", "Eduard",
        "Egbert", "Ehrwald", "Eike", "Emil", "Enno", "Enrico",
        "Ernst", "Eugen", "Falk", "Felix", "Ferdinand", "Franz",
        "Frederick", "Fridolin", "Friedrich", "Fritz", "Gabriel", "Georg",
        "Guido", "Gunthar", "Gustav", "Hagen", "Haimo", "Haribald",
        "Hauke", "Heiner", "Heinrich", "Helmut", "Hendrick", "Henning",
        "Henri", "Henrick", "Herbert", "Hermann", "Hugo", "Irmin",
        "Johann", "Johannes", "Joseph", "Julius", "Justus", "Karl",
        "Kaspar", "Kevin", "Knut", "Konrad", "Konstantin", "Korbinian",
        "Kuno", "Kurt", "Leif", "Lennard", "Leonhard", "Leopold",
        "Levin", "Lian", "Lorenz", "Lothar", "Ludwig", "Luise",
        "Matthias", "Maximilian", "Moritz", "Ole", "Oskar", "Oswin",
        "Otto", "Paul", "Peter", "Philipp", "Raimund", "Rainer",
        "Ralf", "Reinhard", "Richard", "Robert", "Rune", "Sungard",
        "Theobald", "Theodor", "Thiemo", "Thilo", "Timm", "Tjark",
        "Tristan", "Walbert", "Wilhelm",
    ],
    "female": [
        "Adelheid", "Adelma", "Agnes", "Alida", "Alma", "Almut",
        "Amalia", "Amalie", "Anna", "Antonia", "Augusta", "Bernarda",
        "Berta", "Bianca", "Brunhilde", "Charlotte", "Dorothea", "Edda",
        "Edeltraud", "Eila", "Eleonor", "Eleonore", "Elisa", "Elisabeth",
        "Elke", "Elsa", "Elvira", "Emma", "Emmeline", "Ernestine",
        "Evke", "Fara", "Finja", "Franka", "Franziska", "Frauke",
        "Frederike", "Freya", "Frieda", "Friederike", "Friedrun", "Gertrud",
        "Gesa", "Gisela", "Gislind", "Grete", "Gundula", "Hanna",
        "Hedda", "Heidemarie", "Heidrun", "Helena", "Henriette", "Henrike",
        "Hildegrad", "Hiltrud", "Ida", "Imke", "Ina", "Ingeborg",
        "Irma", "Irmgard", "Isabella", "Isolde", "Johanna", "Josephine",
        "Karla", "Karolina", "Katharina", "Klara", "Konstanze", "Kriemhild",
        "Kunigunde", "Kaethe", "Lotte", "Luisa", "Margarete", "Maria",
        "Marie", "Martha", "Mathilda", "Merlinde", "Milda", "Oda",
        "Paula", "Rosalinde", "Rosamunde", "Roswitha", "Ruth", "Sabine",
        "Selma", "Sigrid", "Silke", "Susanne", "Thea", "Thekla",
        "Theresa", "Thialda", "Ulrike", "Ursula", "Vanadis", "Viktoria",
        "Waltraud", "Wilhelmine", "Wilma",
    ]
}

LAST_NAMES = [
    "Mueller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer",
    "Wagner", "Becker", "Schulz", "Hoffmann", "Schaefer", "Bauer",
    "Koch", "Richter", "Klein", "Wolf", "Schroeder", "Neumann",
    "Schwarz", "Braun", "Hofmann", "Zimmermann", "Schmitt", "Hartmann",
    "Krueger", "Schmid", "Werner", "Lange", "Schmitz", "Meier",
    "Krause", "Maier", "Lehmann", "Huber", "Mayer", "Herrmann",
    "Koehler", "Walter", "Koenig", "Schulze", "Fuchs", "Kaiser",
    "Lang", "Weiss", "Peters", "Scholz", "Jung", "Moeller",
    "Hahn", "Keller", "Vogel", "Schubert", "Roth", "Frank",
    "Friedrich", "Beck", "Guenther", "Berger", "Winkler", "Lorenz",
    "Baumann", "Schuster", "Kraus", "Boehm", "Simon", "Franke",
    "Albrecht", "Winter", "Ludwig", "Martin", "Kraemer", "Schumacher",
    "Vogt", "Jaeger", "Stein", "Otto", "Gross", "Sommer",
    "Haas", "Graf", "Heinrich", "Seidel", "Schreiber", "Ziegler",
    "Brandt", "Kuhn", "Schulte", "Dietrich", "Kuehn", "Engel",
    "Pohl", "Horn", "Sauer", "Arnold", "Thomas", "Bergmann",
    "Busch", "Pfeiffer", "Voigt", "Goetz", "Seifert", "Lindner",
    "Ernst", "Huebner", "Kramer", "Franz", "Beyer", "Wolff",
    "Peter", "Jansen", "Kern", "Barth", "Wenzel", "Hermann",
    "Ott", "Paul", "Riedel", "Wilhelm", "Hansen", "Nagel",
    "Grimm", "Lenz", "Ritter", "Bock", "Langer", "Kaufmann",
    "Mohr", "Foerster", "Zimmer", "Haase", "Lutz", "Kruse",
    "Jahn", "Schumann", "Fiedler", "Thiel", "Hoppe", "Kraft",
    "Michel", "Marx", "Fritz", "Arndt", "Eckert", "Schuetz",
    "Walther", "Petersen", "Berg", "Schindler", "Kunz", "Reuter",
    "Sander", "Schilling", "Reinhardt", "Frey", "Ebert", "Boettcher",
    "Thiele", "Gruber", "Schramm", "Hein", "Bayer", "Froehlich",
    "Voss", "Herzog", "Hesse", "Maurer", "Rudolph", "Nowak",
    "Geiger", "Beckmann", "Kunze", "Seitz", "Stephan", "Buettner",
    "Bender", "Gaertner", "Bachmann", "Behrens", "Scherer", "Adam",
    "Stahl", "Steiner", "Kurz", "Dietz", "Brunner", "Witt",
    "Moser", "Fink", "Ullrich", "Kirchner", "Loeffler", "Heinz",
    "Schultz", "Ulrich", "Reichert", "Schwab", "Breuer", "Gerlach",
    "Brinkmann", "Goebel", "Blum", "Brand", "Naumann", "Stark",
    "Wirth", "Schenk", "Binder", "Koerner", "Schlueter", "Rieger",
    "Urban", "Boehme", "Jakob", "Schroeter", "Krebs", "Wegner",
    "Heller", "Kopp", "Link", "Wittmann", "Unger", "Reimann",
    "Ackermann", "Hirsch", "Schiller", "Doering", "May", "Bruns",
    "Wendt", "Wolter", "Menzel", "Pfeifer", "Sturm", "Buchholz",
    "Rose", "Meissner", "Janssen", "Bach", "Engelhardt", "Bischoff",
    "Bartsch", "John", "Kohl", "Kolb", "Muench", "Vetter",
    "Hildebrandt", "Renner", "Weiss", "Kiefer", "Rau", "Hinz",
    "Wilke", "Gebhardt", "Siebert", "Baier", "Koester", "Rohde",
    "Will", "Fricke", "Freitag", "Nickel", "Reich", "Funk",
    "Linke", "Keil", "Hennig", "Witte", "Stoll", "Schreiner",
    "Held", "Noack", "Brueckner", "Decker", "Neubauer", "Westphal",
    "Heinze", "Baum", "Schoen", "Wimmer", "Marquardt", "Stadler",
    "Schlegel", "Kremer", "Ahrens", "Hammer", "Roeder", "Pieper",
    "Kirsch", "Fuhrmann", "Henning", "Krug", "Popp", "Conrad",
    "Karl", "Krieger", "Mann", "Wiedemann", "Lemke", "Erdmann",
    "Mertens", "Hess", "Esser", "Hanke", "Strauss", "Miller",
    "Berndt", "Konrad", "Jacob", "Philipp", "Metzger", "Henke",
    "Wiese", "Hauser", "Dittrich", "Albert", "Klose", "Bader",
    "Herbst", "Henkel", "Kroeger", "Wahl", "Bartels", "Harms",
    "Fritsch", "Adler", "Grossmann", "Burger", "Schrader", "Probst",
    "Martens", "Baur", "Burkhardt", "Hess", "Mayr", "Nolte",
    "Heine", "Kuhlmann", "Klaus", "Kuehne", "Kluge", "Bernhardt",
    "Blank", "Hamann", "Steffen", "Brenner", "Rauch", "Reiter",
    "Preuss", "Jost", "Wild", "Hummel", "Beier", "Krauss",
    "Lindemann", "Herold", "Christ", "Niemann", "Funke", "Haupt",
    "Janssen", "Vollmer", "Straub", "Strobel", "Wiegand", "Merz",
    "Haag", "Holz", "Knoll", "Zander", "Rausch", "Bode",
    "Beer", "Betz", "Anders", "Wetzel", "Hartung", "Glaser",
    "Fleischer", "Rupp", "Reichel", "Lohmann", "Diehl", "Jordan",
    "Eder", "Rothe", "Weis", "Heinemann", "Doerr", "Metz",
    "Kroll", "Freund", "Wegener", "Hohmann", "Geissler", "Schueler",
    "Schade", "Raab", "Feldmann", "Zeller", "Neubert", "Rapp",
    "Kessler", "Heck", "Meister", "Stock", "Roemer", "Seiler",
    "Altmann", "Behrendt", "Jacobs", "Mai", "Baer", "Wunderlich",
    "Schuette", "Lauer", "Benz", "Weise", "Voelker", "Sonntag",
    "Buehler", "Gerber", "Kellner", "Bittner", "Schweizer", "Kessler",
    "Hagen", "Wieland", "Born", "Merkel", "Falk", "Busse",
    "Gross", "Eichhorn", "Greiner", "Moritz", "Forster", "Stumpf",
    "Seidl", "Scharf", "Hentschel", "Buck", "Voss", "Hartwig",
    "Heil", "Eberhardt", "Oswald", "Lechner", "Block", "Heim",
    "Steffens", "Weigel", "Pietsch", "Brandl", "Schott", "Gottschalk",
    "Bertram", "Ehlers", "Fleischmann", "Albers", "Weidner", "Hiller",
    "Seeger", "Geyer", "Juergens", "Baumgartner", "Mack", "Schuler",
    "Appel", "Pape", "Dorn", "Wulf", "Opitz", "Wiesner",
    "Hecht", "Moll", "Gabriel", "Auer", "Engelmann", "Singer",
    "Neuhaus", "Giese", "Schuetze", "Geisler", "Ruf", "Heuer",
    "Noll", "Scheffler", "Sauter", "Reimer", "Klemm", "Schaller",
    "Hempel", "Kretschmer", "Runge", "Springer", "Riedl", "Steinbach",
    "Michels", "Barthel",
]
LAST_NAME_PREFIXES = [
    "Ober", "Unter", "Nieder", 
]
LAST_NAME_POSTFIXES = [
    "kamp", "mann", "berg", "hammer", "bach", "rath"
]

def gen_german_name():
    def gen_last_single():
        result = random.choice(LAST_NAMES)
        # add last name prefix?
        if random.randint(0, 99) < 10:
            result = random.choice(LAST_NAME_PREFIXES) + result.lower()
        # add last name postfix?
        elif random.randint(0, 99) < 3:
            postfix = random.choice(LAST_NAME_POSTFIXES)
            if not result.endswith(postfix):
                result += postfix
        return result

    gender = random.choice(list(FIRST_NAMES.keys()))
    first_name = random.choice(FIRST_NAMES[gender])
    is_dashed = random.randint(0, 99) < 30
    first_name += "-" if is_dashed else " "
    first_name += random.choice(FIRST_NAMES[gender])
    first_name += " " + random.choice(FIRST_NAMES[gender])

    last_name = gen_last_single()
    # combine two last names?
    if random.randint(0, 99) < 10:
        last_name += "-" + gen_last_single()

    return (first_name, last_name)
