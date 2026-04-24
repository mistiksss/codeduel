--
-- PostgreSQL database dump
--

\restrict TqlS2VqAojMWtmdXv1ZwoIO1i8ayyVego03OrTS9y6Q1OBlwaeLnD2yhhhUjVkZ

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO postgres;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: attempts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.attempts (
    id integer NOT NULL,
    user_id integer NOT NULL,
    task_id integer NOT NULL,
    code text NOT NULL,
    language character varying(20) NOT NULL,
    status character varying(50) NOT NULL,
    execution_time double precision,
    memory_used integer,
    tests_passed integer,
    total_tests integer,
    score integer,
    error_message text,
    submitted_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.attempts OWNER TO postgres;

--
-- Name: attempts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.attempts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.attempts_id_seq OWNER TO postgres;

--
-- Name: attempts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.attempts_id_seq OWNED BY public.attempts.id;


--
-- Name: match_results; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_results (
    id integer NOT NULL,
    match_id integer NOT NULL,
    user_id integer NOT NULL,
    attempt_id integer NOT NULL,
    score integer,
    tests_passed integer,
    total_tests integer,
    execution_time double precision,
    submitted_at timestamp without time zone
);


ALTER TABLE public.match_results OWNER TO postgres;

--
-- Name: match_results_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_results_id_seq OWNER TO postgres;

--
-- Name: match_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_results_id_seq OWNED BY public.match_results.id;


--
-- Name: matches; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.matches (
    id integer NOT NULL,
    user_id integer NOT NULL,
    opponent_id integer,
    task_id integer NOT NULL,
    result character varying(10),
    user_rating_change integer NOT NULL,
    opponent_rating_change integer,
    match_duration integer,
    played_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    started_at timestamp without time zone,
    ended_at timestamp without time zone,
    CONSTRAINT matches_result_check CHECK (((result)::text = ANY (ARRAY[('win'::character varying)::text, ('loss'::character varying)::text, ('draw'::character varying)::text])))
);


ALTER TABLE public.matches OWNER TO postgres;

--
-- Name: matches_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.matches_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.matches_id_seq OWNER TO postgres;

--
-- Name: matches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.matches_id_seq OWNED BY public.matches.id;


--
-- Name: matchmaking_queue; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.matchmaking_queue (
    id integer NOT NULL,
    user_id integer NOT NULL,
    elo integer NOT NULL,
    task_id integer,
    difficulty character varying(20),
    joined_at timestamp without time zone,
    last_ping timestamp without time zone,
    status character varying(20)
);


ALTER TABLE public.matchmaking_queue OWNER TO postgres;

--
-- Name: matchmaking_queue_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.matchmaking_queue_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.matchmaking_queue_id_seq OWNER TO postgres;

--
-- Name: matchmaking_queue_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.matchmaking_queue_id_seq OWNED BY public.matchmaking_queue.id;


--
-- Name: rating; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rating (
    id integer NOT NULL,
    user_id integer NOT NULL,
    total_points integer DEFAULT 0,
    rank_position integer,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.rating OWNER TO postgres;

--
-- Name: rating_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.rating_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.rating_id_seq OWNER TO postgres;

--
-- Name: rating_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.rating_id_seq OWNED BY public.rating.id;


--
-- Name: tasks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tasks (
    id integer NOT NULL,
    title character varying(200) NOT NULL,
    description text NOT NULL,
    input_description text NOT NULL,
    output_description text NOT NULL,
    difficulty_level character varying(20),
    points integer NOT NULL,
    time_limit integer DEFAULT 1000,
    memory_limit integer DEFAULT 256,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    example text,
    answer text,
    difficulty character varying(20) DEFAULT 'medium'::character varying,
    hide boolean DEFAULT false NOT NULL,
    CONSTRAINT tasks_difficulty_level_check CHECK (((difficulty_level)::text = ANY (ARRAY[('легкая'::character varying)::text, ('средняя'::character varying)::text, ('сложная'::character varying)::text])))
);


ALTER TABLE public.tasks OWNER TO postgres;

--
-- Name: tasks_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tasks_id_seq OWNER TO postgres;

--
-- Name: tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tasks_id_seq OWNED BY public.tasks.id;


--
-- Name: test_cases; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.test_cases (
    id integer NOT NULL,
    task_id integer NOT NULL,
    input_data text NOT NULL,
    expected_output text NOT NULL,
    is_hidden boolean DEFAULT false,
    points integer DEFAULT 10
);


ALTER TABLE public.test_cases OWNER TO postgres;

--
-- Name: test_cases_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.test_cases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.test_cases_id_seq OWNER TO postgres;

--
-- Name: test_cases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.test_cases_id_seq OWNED BY public.test_cases.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    elo integer DEFAULT 1000,
    best_elo integer DEFAULT 1000,
    wins integer DEFAULT 0,
    losses integer DEFAULT 0,
    games_played integer DEFAULT 0,
    title character varying(20) DEFAULT 'Новичок'::character varying,
    draws integer DEFAULT 0,
    is_online boolean DEFAULT false,
    last_seen timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    onboarding_completed boolean DEFAULT false,
    preferred_language character varying(20) DEFAULT 'python'::character varying,
    experience_level character varying(20) DEFAULT 'novice'::character varying,
    current_streak integer DEFAULT 0,
    is_premium boolean DEFAULT false,
    premium_until timestamp without time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: attempts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attempts ALTER COLUMN id SET DEFAULT nextval('public.attempts_id_seq'::regclass);


--
-- Name: match_results id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_results ALTER COLUMN id SET DEFAULT nextval('public.match_results_id_seq'::regclass);


--
-- Name: matches id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matches ALTER COLUMN id SET DEFAULT nextval('public.matches_id_seq'::regclass);


--
-- Name: matchmaking_queue id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matchmaking_queue ALTER COLUMN id SET DEFAULT nextval('public.matchmaking_queue_id_seq'::regclass);


--
-- Name: rating id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rating ALTER COLUMN id SET DEFAULT nextval('public.rating_id_seq'::regclass);


--
-- Name: tasks id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tasks ALTER COLUMN id SET DEFAULT nextval('public.tasks_id_seq'::regclass);


--
-- Name: test_cases id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_cases ALTER COLUMN id SET DEFAULT nextval('public.test_cases_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: attempts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.attempts (id, user_id, task_id, code, language, status, execution_time, memory_used, tests_passed, total_tests, score, error_message, submitted_at) FROM stdin;
43	1	6	def main():\n        # Введите ваш код здесь\n        n = int(input())\n        print(n * 2)\n\n    if __name__ == "__main__":\n        main()	python	runtime_error	0.0895666666666667	\N	0	30	0	File "C:\\Users\\E67B~1\\AppData\\Local\\Temp\\tmpit8t7on8.py", line 6\r\n    if __name__ == "__main__":\r\n                              ^\r\nIndentationError: unindent does not match any outer indentation level	2026-01-19 21:38:02.631645
44	1	6	nums = map(int, input().split())\n\nresult = []\nfor n in nums:\n    if n % 2 == 0:\n        result.append("четное")\n    else:\n        result.append("нечетное")\n\nprint(" ".join(result))\n	python	accepted	0.060966666666666676	\N	30	30	22		2026-01-19 21:40:49.53988
45	7	6	import sys\n\ndata = sys.stdin.read().split()\nresult = []\n\nfor x in data:\n    n = int(x)\n    result.append("четное" if n % 2 == 0 else "нечетное")\n\nprint(" ".join(result))\n	python	accepted	0.05966666666666666	\N	30	30	20		2026-01-19 21:53:07.714666
47	1	11	import sys\n\ndef gcd(a: int, b: int) -> int:\n    while b:\n        a, b = b, a % b\n    return a\n\ndata = sys.stdin.read().split()\nnums = list(map(int, data))\n\nans = []\nfor i in range(0, len(nums), 2):\n    a = nums[i]\n    b = nums[i + 1]\n    ans.append(str(gcd(a, b)))\n\nprint(" ".join(ans))\n	python	partially_correct	0.06824000000000002	\N	24	25	79		2026-01-19 22:50:54.913369
48	1	11	import sys\n\ndef gcd(a: int, b: int) -> int:\n    while b:\n        a, b = b, a % b\n    return a\n\nnums = list(map(int, sys.stdin.read().split()))\nif not nums:\n    sys.exit(0)\n\npairs = []\n\n# Вариант 1: первый элемент — количество пар t, и дальше ровно 2*t чисел\nt = nums[0]\nif len(nums) == 1 + 2 * t:\n    for i in range(1, len(nums), 2):\n        pairs.append((nums[i], nums[i + 1]))\nelse:\n    # Вариант 2: просто поток чисел a b a b ...\n    # (на всякий случай игнорируем лишнее, если вдруг нечётное количество)\n    m = (len(nums) // 2) * 2\n    for i in range(0, m, 2):\n        pairs.append((nums[i], nums[i + 1]))\n\nout = [str(gcd(a, b)) for a, b in pairs]\n\n# Обычно для нескольких тестов ждут построчно — это безопаснее\nsys.stdout.write("\\n".join(out))\n	python	partially_correct	0.062	\N	24	25	79		2026-01-19 23:01:55.605673
49	1	11	import sys\n\ndef gcd(a: int, b: int) -> int:\n    while b:\n        a, b = b, a % b\n    return a\n\nnums = list(map(int, sys.stdin.read().split()))\nif not nums:\n    sys.exit(0)\n\npairs = []\n\n# Вариант 1: первый элемент — количество пар t, и дальше ровно 2*t чисел\nt = nums[0]\nif len(nums) == 1 + 2 * t:\n    for i in range(1, len(nums), 2):\n        pairs.append((nums[i], nums[i + 1]))\nelse:\n    # Вариант 2: просто поток чисел a b a b ...\n    # (на всякий случай игнорируем лишнее, если вдруг нечётное количество)\n    m = (len(nums) // 2) * 2\n    for i in range(0, m, 2):\n        pairs.append((nums[i], nums[i + 1]))\n\nout = [str(gcd(a, b)) for a, b in pairs]\n\n# Обычно для нескольких тестов ждут построчно — это безопаснее\nsys.stdout.write("\\n".join(out))\n	python	partially_correct	0.05848000000000002	\N	24	25	79		2026-01-19 23:02:01.747496
50	1	12		forfeit	FORFEIT_WIN	0	0	29	29	80	\N	2026-01-20 11:06:23.702177
51	7	12		forfeit	FORFEIT_LOSS	0	0	0	29	0	\N	2026-01-20 11:06:23.71443
52	1	7		forfeit	FORFEIT_WIN	0	0	30	30	50	\N	2026-01-20 11:10:34.504536
53	7	7		forfeit	FORFEIT_LOSS	0	0	0	30	0	\N	2026-01-20 11:10:34.509241
54	1	23		forfeit	FORFEIT_WIN	0	0	30	30	20	\N	2026-01-27 12:21:41.634846
55	7	23		forfeit	FORFEIT_LOSS	0	0	0	30	0	\N	2026-01-27 12:21:41.667278
56	9	21		forfeit	FORFEIT_WIN	0	0	32	32	20	\N	2026-02-01 22:27:05.652162
57	7	21		forfeit	FORFEIT_LOSS	0	0	0	32	0	\N	2026-02-01 22:27:05.664261
58	10	19		forfeit	FORFEIT_WIN	0	0	44	44	50	\N	2026-03-10 22:13:33.896645
59	1	19		forfeit	FORFEIT_LOSS	0	0	0	44	0	\N	2026-03-10 22:13:33.901432
60	10	21		forfeit	FORFEIT_WIN	0	0	32	32	20	\N	2026-03-10 23:18:13.374906
61	1	21		forfeit	FORFEIT_LOSS	0	0	0	32	0	\N	2026-03-10 23:18:13.378062
62	3	8	def main():\n        # Введите ваш код здесь\n        n = int(input())\n        print(n * 2)\n\n    if __name__ == "__main__":\n        main()	python	runtime_error	0.029096774193548405	\N	0	31	0	File "C:\\Users\\C058~1\\AppData\\Local\\Temp\\tmpysjd88je.py", line 6\r\n    if __name__ == "__main__":\r\n                              ^\r\nIndentationError: unindent does not match any outer indentation level	2026-04-08 22:00:24.490329
63	1	8	n = int(input())\na, b = 0, 1\nfor _ in range(n):\n    a, b = b, a + b\nprint(a)	python	accepted	0.01790322580645162	\N	31	31	50		2026-04-08 22:04:26.018789
64	12	4	print(2)	python	wrong_answer	0.017566666666666675	\N	0	30	0		2026-04-22 20:36:17.074421
65	12	4	print(2)	python	wrong_answer	0.016933333333333342	\N	0	30	0		2026-04-22 21:16:40.033693
66	1	22		forfeit	FORFEIT_WIN	0	\N	30	30	50	\N	2026-04-22 21:42:18.495555
67	12	22		forfeit	FORFEIT_LOSS	0	\N	0	30	0	\N	2026-04-22 21:42:18.498517
\.


--
-- Data for Name: match_results; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.match_results (id, match_id, user_id, attempt_id, score, tests_passed, total_tests, execution_time, submitted_at) FROM stdin;
1	18	7	45	20	30	30	0.05966666666666666	2026-01-19 21:53:09.665673
3	20	1	49	79	24	25	0.05848000000000002	2026-01-19 23:02:03.241738
4	24	1	50	80	29	29	0	2026-01-20 11:06:23.702177
5	24	7	51	0	0	29	0	2026-01-20 11:06:23.71443
6	25	1	52	50	30	30	0	2026-01-20 11:10:34.504536
7	25	7	53	0	0	30	0	2026-01-20 11:10:34.509241
8	26	1	54	20	30	30	0	2026-01-27 12:21:41.634846
9	26	7	55	0	0	30	0	2026-01-27 12:21:41.667278
10	28	9	56	20	32	32	0	2026-02-01 22:27:05.652162
11	28	7	57	0	0	32	0	2026-02-01 22:27:05.664261
12	29	10	58	50	44	44	0	2026-03-10 22:13:33.896645
13	29	1	59	0	0	44	0	2026-03-10 22:13:33.901432
14	30	10	60	20	32	32	0	2026-03-10 23:18:13.374906
15	30	1	61	0	0	32	0	2026-03-10 23:18:13.378062
16	31	3	62	0	0	31	0.029096774193548405	2026-04-08 22:00:25.418873
17	31	1	63	50	31	31	0.01790322580645162	2026-04-08 22:04:26.592874
18	32	1	66	50	30	30	0	2026-04-22 21:42:18.495555
19	32	12	67	0	0	30	0	2026-04-22 21:42:18.498517
\.


--
-- Data for Name: matches; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.matches (id, user_id, opponent_id, task_id, result, user_rating_change, opponent_rating_change, match_duration, played_at, created_at, started_at, ended_at) FROM stdin;
21	1	7	22	loss	-22	22	0	2026-01-20 09:50:15.471758	2026-01-20 09:50:15.481782	2026-01-20 12:50:15.481782	2026-01-20 10:30:45.121672
20	1	7	11	win	11	-11	29395	2026-01-19 22:40:11.031801	2026-01-19 22:40:11.064703	2026-01-20 01:40:11.064703	2026-01-20 09:50:06.618769
24	1	7	12	win	13	-13	0	2026-01-20 11:05:47.331	2026-01-20 11:05:47.342199	2026-01-20 14:05:47.342199	2026-01-20 11:06:23.695042
22	1	7	20	win	12	-12	0	2026-01-20 10:43:09.952758	2026-01-20 10:43:09.970585	2026-01-20 13:43:09.970585	2026-01-20 10:43:37.626804
18	1	7	6	loss	-25	25	4744	2026-01-19 14:49:15.068883	2026-01-19 14:49:15.101871	2026-01-19 20:49:15.101871	2026-01-19 22:08:19.203907
27	1	7	6	draw	-6	0	91425	2026-01-27 12:21:51.36099	2026-01-27 12:21:51.375076	2026-01-27 21:21:51.375076	2026-01-28 22:45:37.294108
26	1	7	23	win	11	-11	0	2026-01-27 12:17:50.622476	2026-01-27 12:17:50.651796	2026-01-27 15:17:50.651796	2026-01-27 12:21:41.67547
23	1	7	20	loss	-20	0	0	2026-01-20 10:56:27.324345	2026-01-20 10:56:27.336658	2026-01-20 13:56:27.336658	2026-01-20 10:56:33.783333
25	1	7	7	win	11	-11	0	2026-01-20 11:10:23.366537	2026-01-20 11:10:23.369292	2026-01-20 14:10:23.369292	2026-01-20 11:10:34.512525
28	7	9	21	loss	-17	17	0	2026-02-01 22:26:56.541474	2026-02-01 22:26:56.554055	2026-02-02 01:26:56.554055	2026-02-01 22:27:05.646645
29	1	10	19	loss	-23	23	0	2026-03-10 22:11:39.541926	2026-03-10 22:11:39.546676	2026-03-11 01:11:39.546676	2026-03-10 22:13:33.903445
31	1	3	8	win	11	-11	0	2026-04-08 21:59:31.340751	2026-04-08 21:59:31.346349	2026-04-09 00:59:31.346349	2026-04-08 22:09:17.816764
30	1	10	21	loss	-21	21	0	2026-03-10 23:18:08.99858	2026-03-10 23:18:09.00165	2026-03-11 02:18:09.00165	2026-03-10 23:18:13.380077
32	1	12	22	win	11	-11	0	2026-04-22 21:33:29.424488	2026-04-22 21:33:29.42829	2026-04-23 00:33:29.42829	2026-04-22 21:42:18.50006
\.


--
-- Data for Name: matchmaking_queue; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.matchmaking_queue (id, user_id, elo, task_id, difficulty, joined_at, last_ping, status) FROM stdin;
91	1	1157	\N	easy	2026-01-27 12:21:47.813196	2026-01-27 12:21:47.877395	matched
80	7	1000	\N	any	2026-01-19 14:49:10.761407	2026-01-19 14:49:14.071839	matched
93	9	1000	\N	easy	2026-02-01 22:26:51.405606	2026-02-01 22:26:54.441576	matched
47	5	1000	4	easy	2026-01-15 08:52:45.383362	2026-01-15 08:52:45.383378	matched
50	1	1210	10	medium	2026-01-15 10:30:25.304026	2026-01-15 10:31:05.16733	matched
51	1	1210	6	easy	2026-01-15 10:42:22.227838	2026-01-15 10:42:22.22784	matched
52	6	1000	6	easy	2026-01-15 10:43:49.993537	2026-01-15 10:43:49.993555	matched
53	1	1210	5	easy	2026-01-15 10:44:01.528907	2026-01-15 10:44:01.528913	matched
54	1	1210	6	easy	2026-01-15 10:46:50.764632	2026-01-15 10:46:50.764637	matched
55	6	1000	4	easy	2026-01-15 10:47:07.37072	2026-01-15 10:47:07.370737	matched
61	1	1210	\N	medium	2026-01-19 12:35:30.315785	2026-01-19 12:38:05.271602	matched
63	1	1210	\N	any	2026-01-19 12:38:44.666322	2026-01-19 12:38:44.666335	matched
65	7	1000	\N	any	2026-01-19 13:09:05.520249	2026-01-19 13:09:05.520263	matched
71	1	1210	\N	any	2026-01-19 14:02:46.114358	2026-01-19 14:02:46.114363	matched
72	1	1210	\N	any	2026-01-19 14:02:58.789757	2026-01-19 14:02:58.789766	matched
75	7	1000	\N	any	2026-01-19 14:30:58.112788	2026-01-19 14:30:58.112791	matched
76	7	1000	\N	any	2026-01-19 14:38:55.471055	2026-01-19 14:38:55.471069	matched
83	7	1025	\N	any	2026-01-19 22:10:04.887526	2026-01-19 22:10:08.394115	matched
78	7	1000	\N	any	2026-01-19 14:43:46.111768	2026-01-19 14:43:46.111782	matched
84	7	1048	\N	any	2026-01-19 22:40:08.728162	2026-01-19 22:40:08.797923	matched
85	7	1037	\N	any	2026-01-20 09:50:10.779409	2026-01-20 09:50:14.147116	matched
86	7	1059	\N	any	2026-01-20 10:43:06.932714	2026-01-20 10:43:06.955579	matched
87	7	1047	\N	any	2026-01-20 10:56:23.501328	2026-01-20 10:56:27.13982	matched
88	1	1122	\N	any	2026-01-20 11:05:39.209735	2026-01-20 11:05:46.150509	matched
89	7	1034	\N	any	2026-01-20 11:10:20.927953	2026-01-20 11:10:21.028918	matched
90	1	1146	\N	easy	2026-01-27 12:17:46.272584	2026-01-27 12:17:49.778071	matched
109	1	1118	\N	any	2026-04-22 21:33:25.786287	2026-04-22 21:33:25.790619	matched
100	10	1000	\N	medium	2026-03-10 22:11:37.26984	2026-03-10 22:11:37.276634	matched
101	10	1023	\N	easy	2026-03-10 23:18:03.883803	2026-03-10 23:18:06.899866	matched
104	3	1000	\N	easy	2026-04-08 21:59:28.734802	2026-04-08 21:59:28.741558	matched
\.


--
-- Data for Name: rating; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.rating (id, user_id, total_points, rank_position, last_updated) FROM stdin;
\.


--
-- Data for Name: tasks; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tasks (id, title, description, input_description, output_description, difficulty_level, points, time_limit, memory_limit, created_at, example, answer, difficulty, hide) FROM stdin;
4	Сумма двух чисел	Даны два целых числа. Выведите их сумму.	На вход подаются два целых числа a и b, разделенных пробелом.	Выведите одно целое число — сумму a и b.	легкая	20	1	64	2026-01-14 21:45:20.663988	2 3\n    -5 10\n    0 0\n    -100 -200	5\n    5\n    0\n    -300	easy	f
5	Максимум из двух	Даны два целых числа. Найдите наибольшее из них.	На вход подаются два целых числа a и b, разделенных пробелом.	Выведите максимальное из двух чисел.	легкая	20	1	64	2026-01-14 21:45:57.294577	8 5\n    -3 2\n    7 7\n    -10 -5	8\n    2\n    7\n    -5	easy	f
6	Четное или нечетное	Дано целое число. Определите, является ли оно четным.	На вход подается одно целое число n.	Выведите "четное", если число четное, и "нечетное", если нечетное.	легкая	20	1	64	2026-01-14 21:46:15.760686	6\n    7\n    0\n    -4	четное\n    нечетное\n    четное\n    четное	easy	f
7	Сумма цифр числа	Дано целое число. Найдите сумму его цифр.	На вход подается одно целое число n (-10^9 ≤ n ≤ 10^9).	Выведите сумму цифр числа n (без учета знака).	средняя	50	1	64	2026-01-14 21:46:43.972036	123\n    -456\n    0\n    999	6\n    15\n    0\n    27	medium	f
8	Числа Фибоначчи	Найдите n-е число Фибоначчи. F(0) = 0, F(1) = 1, F(n) = F(n-1) + F(n-2).	На вход подается одно целое число n (0 ≤ n ≤ 30).	Выведите n-е число Фибоначчи.	средняя	50	1	64	2026-01-14 21:47:02.004294	0\n    1\n    6\n    10	0\n    1\n    8\n    55	medium	f
9	Простое число	Определите, является ли заданное число простым.	На вход подается одно целое число n (1 ≤ n ≤ 10^6).	Выведите "YES", если число простое, и "NO", если составное.	сложная	80	2	64	2026-01-14 21:47:19.629598	7\n    1\n    10\n    2	YES\n    NO\n    NO\n    YES	hard	f
10	Палиндром	Дана строка. Определите, является ли она палиндромом (читается одинаково слева направо и справа налево).	На вход подается одна строка s (1 ≤ len(s) ≤ 1000).	Выведите "YES", если строка палиндром, иначе "NO".	средняя	50	1	64	2026-01-14 21:47:38.18191	racecar\n    hello\n    a\n    12321	YES\n    NO\n    YES\n    YES	medium	f
11	НОД двух чисел	Найдите наибольший общий делитель (НОД) двух чисел.	На вход подаются два целых числа a и b, разделенных пробелом (1 ≤ a, b ≤ 10^9).	Выведите НОД(a, b).	сложная	80	2	64	2026-01-14 21:47:53.184967	12 18\n    35 49\n    17 23\n    1071 462	6\n    7\n    1\n    21	hard	f
12	Анаграммы	Даны две строки. Определите, являются ли они анаграммами (состоят из одних и тех же букв в разном порядке).	На вход подаются две строки a и b, каждая на отдельной строке.	Выведите "YES", если строки анаграммы, иначе "NO".	сложная	80	2	64	2026-01-14 21:48:16.341457	listen\n    silent\n    hello\n    world\n    abc\n    cba\n    test\n    tset	YES\n    NO\n    YES\n    YES	hard	f
14	Минимум трех чисел	Даны три целых числа. Найдите наименьшее из них.	На вход подаются три целых числа a, b, c, разделенных пробелами.	Выведите минимальное из трех чисел.	легкая	20	1	64	2026-01-20 09:40:11.179519	5 2 8\n-3 0 3\n7 7 7\n10 -5 0	2\n-3\n7\n-5	easy	t
15	Сумма ряда	Вычислите сумму чисел от 1 до n.	На вход подается одно целое число n (1 ≤ n ≤ 1000).	Выведите сумму чисел от 1 до n.	средняя	50	1	64	2026-01-20 09:40:11.179519	5\n10\n1\n100	15\n55\n1\n5050	medium	t
16	Переворот числа	Дано целое число. Переверните его цифры.	На вход подается одно целое число n (-10^9 ≤ n ≤ 10^9).	Выведите число с цифрами в обратном порядке.	средняя	50	1	64	2026-01-20 09:40:11.179519	123\n-456\n1000\n0	321\n-654\n1\n0	medium	t
17	Количество делителей	Найдите количество всех делителей заданного числа.	На вход подается одно целое положительное число n (1 ≤ n ≤ 10^6).	Выведите количество всех делителей числа n.	сложная	80	2	64	2026-01-20 09:40:11.179519	12\n1\n17\n36	6\n1\n2\n9	hard	t
18	Сумма четных чисел	Дано число n. Найдите сумму всех четных чисел от 1 до n.	На вход подается одно целое число n (1 ≤ n ≤ 1000).	Выведите сумму всех четных чисел от 1 до n.	легкая	20	1	64	2026-01-20 09:40:11.179519	10\n5\n1\n20	30\n6\n0\n110	easy	t
19	Степень двойки	Определите, является ли заданное число степенью двойки.	На вход подается одно целое положительное число n (1 ≤ n ≤ 10^9).	Выведите "YES", если число является степенью двойки, иначе "NO".	средняя	50	1	64	2026-01-20 09:40:11.179519	8\n6\n1\n256	YES\nNO\nYES\nYES	medium	t
20	Биномиальный коэффициент	Вычислите биномиальный коэффициент C(n, k).	На вход подаются два целых числа n и k, разделенных пробелом (0 ≤ k ≤ n ≤ 20).	Выведите значение C(n, k).	сложная	80	1	64	2026-01-20 09:40:11.179519	5 2\n0 0\n7 3\n10 5	10\n1\n35\n252	hard	t
21	Сумма нечетных чисел	Дано число n. Найдите сумму всех нечетных чисел от 1 до n.	На вход подается одно целое число n (1 ≤ n ≤ 1000).	Выведите сумму всех нечетных чисел от 1 до n.	легкая	20	1	64	2026-01-20 09:40:11.179519	10\n5\n1\n9	25\n9\n1\n25	easy	t
22	Проверка треугольника	По трем сторонам определите, существует ли треугольник.	На вход подаются три целых положительных числа a, b, c, разделенных пробелами (1 ≤ a, b, c ≤ 1000).	Выведите "YES", если треугольник существует, иначе "NO".	средняя	50	1	64	2026-01-20 09:40:11.179519	3 4 5\n1 2 3\n5 5 5\n10 1 1	YES\nNO\nYES\nNO	medium	t
23	Наибольшая цифра числа	Найдите наибольшую цифру в заданном числе.	На вход подается одно целое положительное число n (1 ≤ n ≤ 10^9).	Выведите наибольшую цифру числа n.	легкая	20	1	64	2026-01-20 09:40:11.179519	12345\n987\n1000\n9	5\n9\n1\n9	easy	t
\.


--
-- Data for Name: test_cases; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.test_cases (id, task_id, input_data, expected_output, is_hidden, points) FROM stdin;
51	4	2 3	5	f	1
52	4	-5 10	5	t	1
53	4	0 0	0	t	1
54	4	-100 -200	-300	t	1
55	4	7 -7	0	t	1
56	4	100 200	300	t	1
57	4	-1 -1	-2	t	1
58	4	999 1	1000	t	1
59	4	-50 50	0	t	1
60	4	123 456	579	t	1
61	4	-999 0	-999	t	1
62	4	0 999	999	t	1
63	4	25 75	100	t	1
64	4	-333 -667	-1000	t	1
65	4	42 -42	0	t	1
66	4	1000 -500	500	t	1
67	4	-1 1	0	t	1
68	4	9999 1	10000	t	1
69	4	-1000 500	-500	t	1
70	4	77 23	100	t	1
71	4	-10 -90	-100	t	1
72	4	500 500	1000	t	1
73	4	-250 250	0	t	1
74	4	0 -100	-100	t	1
75	4	888 112	1000	t	2
76	4	-777 -223	-1000	t	2
77	4	123456 654321	777777	t	2
78	4	-999999 1	-999998	t	2
79	4	2147483647 0	2147483647	t	3
80	4	-2147483648 1	-2147483647	t	3
81	5	8 5	8	f	1
82	5	-3 2	2	t	1
83	5	7 7	7	t	1
84	5	-10 -5	-5	t	1
85	5	0 0	0	t	1
86	5	100 -100	100	t	1
87	5	-1 -9	-1	t	1
88	5	999 1	999	t	1
89	5	-50 0	0	t	1
90	5	42 24	42	t	1
91	5	0 1	1	t	1
92	5	-100 -200	-100	t	1
93	5	77 77	77	t	1
94	5	123 321	321	t	1
95	5	-5 -3	-3	t	1
96	5	1000 999	1000	t	1
97	5	-42 42	42	t	1
98	5	0 -1	0	t	1
99	5	500 500	500	t	1
100	5	-10 -10	-10	t	1
101	5	88 99	99	t	1
102	5	-77 -66	-66	t	1
103	5	1 0	1	t	1
104	5	-999 -1000	-999	t	1
105	5	25 75	75	t	2
106	5	100 101	101	t	2
107	5	-2147483648 -2147483647	-2147483647	t	2
108	5	2147483647 2147483646	2147483647	t	3
109	5	-1 -2147483648	-1	t	3
110	5	999999999 1000000000	1000000000	t	3
111	6	6	четное	f	1
112	6	7	нечетное	t	1
113	6	0	четное	t	1
114	6	-4	четное	t	1
115	6	1	нечетное	t	1
116	6	-1	нечетное	t	1
117	6	2	четное	t	1
118	6	-2	четное	t	1
119	6	100	четное	t	1
120	6	-100	четное	t	1
121	6	99	нечетное	t	1
122	6	-99	нечетное	t	1
123	6	256	четное	t	1
124	6	-256	четное	t	1
125	6	13	нечетное	t	1
126	6	-13	нечетное	t	1
127	6	42	четное	t	1
128	6	-42	четное	t	1
129	6	777	нечетное	t	1
130	6	-777	нечетное	t	1
131	6	1000	четное	t	1
132	6	-1000	четное	t	1
133	6	101	нечетное	t	1
134	6	-101	нечетное	t	2
135	6	2147483647	нечетное	t	2
136	6	-2147483648	четное	t	2
137	6	999999999	нечетное	t	2
138	6	-999999998	четное	t	3
139	6	123456789	нечетное	t	3
140	6	-987654322	четное	t	3
141	7	123	6	f	1
142	7	-456	15	t	1
143	7	0	0	t	1
144	7	999	27	t	1
145	7	1	1	t	1
146	7	-1	1	t	1
147	7	10	1	t	1
148	7	-10	1	t	1
149	7	100	1	t	1
150	7	-100	1	t	1
151	7	111	3	t	1
152	7	-111	3	t	1
153	7	1234	10	t	2
154	7	-1234	10	t	2
155	7	9876	30	t	2
156	7	-9876	30	t	2
157	7	10000	1	t	2
158	7	-10000	1	t	2
159	7	99999	45	t	2
160	7	-99999	45	t	2
161	7	123456	21	t	2
162	7	-123456	21	t	3
163	7	987654321	45	t	3
164	7	-987654321	45	t	3
165	7	1000000000	1	t	3
166	7	-1000000000	1	t	3
167	7	2147483647	46	t	3
168	7	-2147483648	47	t	3
169	7	999999999	81	t	3
170	7	-999999999	81	t	3
171	8	0	0	f	1
172	8	1	1	t	1
173	8	6	8	t	1
174	8	10	55	t	1
175	8	2	1	t	1
176	8	3	2	t	1
177	8	4	3	t	1
178	8	5	5	t	1
179	8	7	13	t	1
180	8	8	21	t	1
181	8	9	34	t	2
182	8	11	89	t	2
183	8	12	144	t	2
184	8	13	233	t	2
185	8	14	377	t	2
186	8	15	610	t	2
187	8	16	987	t	2
188	8	17	1597	t	2
189	8	18	2584	t	3
190	8	19	4181	t	3
191	8	20	6765	t	3
192	8	21	10946	t	3
193	8	22	17711	t	3
194	8	23	28657	t	3
195	8	24	46368	t	3
196	8	25	75025	t	3
197	8	26	121393	t	3
198	8	27	196418	t	3
199	8	28	317811	t	3
200	8	29	514229	t	3
201	8	30	832040	t	3
202	9	7	YES	f	1
203	9	1	NO	t	1
204	9	10	NO	t	1
205	9	2	YES	t	1
206	9	3	YES	t	1
207	9	4	NO	t	1
208	9	5	YES	t	1
209	9	6	NO	t	1
210	9	8	NO	t	2
211	9	9	NO	t	2
212	9	11	YES	t	2
213	9	12	NO	t	2
214	9	13	YES	t	2
215	9	14	NO	t	2
216	9	15	NO	t	2
217	9	16	NO	t	2
218	9	17	YES	t	2
219	9	18	NO	t	2
220	9	19	YES	t	2
221	9	20	NO	t	2
222	9	23	YES	t	3
223	9	29	YES	t	3
224	9	31	YES	t	3
225	9	37	YES	t	3
226	9	41	YES	t	3
227	9	43	YES	t	3
228	9	47	YES	t	3
229	9	53	YES	t	3
230	9	59	YES	t	3
231	9	61	YES	t	3
232	9	67	YES	t	3
233	9	71	YES	t	3
234	9	73	YES	t	3
235	10	racecar	YES	f	1
236	10	hello	NO	t	1
237	10	a	YES	t	1
238	10	12321	YES	t	1
239	10	ab	NO	t	1
240	10	aa	YES	t	1
241	10	aba	YES	t	1
242	10	abc	NO	t	1
243	10	level	YES	t	2
244	10	madam	YES	t	2
245	10	noon	YES	t	2
246	10	radar	YES	t	2
247	10	rotor	YES	t	2
248	10	civic	YES	t	2
249	10	refer	YES	t	2
250	10	deified	YES	t	2
251	10	race a car	NO	t	2
252	10	A man a plan a canal Panama	NO	t	3
253	10	Was it a car or a cat I saw	NO	t	3
254	10	Never odd or even	NO	t	3
255	10	Do geese see God	NO	t	3
256	10	123454321	YES	t	3
257	10	12345654321	YES	t	3
258	10	aaaaaaaaaa	YES	t	3
259	10	abccba	YES	t	3
260	10	abcdcba	YES	t	3
261	10	abcdeedcba	YES	t	3
262	10	abcdefgfedcba	YES	t	3
263	10	not a palindrome	NO	t	3
264	11	12 18	6	f	1
265	11	35 49	7	t	1
266	11	17 23	1	t	1
267	11	1071 462	21	t	1
268	11	8 12	4	t	2
269	11	54 24	6	t	2
270	11	101 103	1	t	2
271	11	100 25	25	t	2
272	11	81 27	27	t	2
273	11	48 18	6	t	2
274	11	144 96	48	t	2
275	11	13 13	13	t	2
276	11	0 5	5	t	2
277	11	5 0	5	t	2
278	11	0 0	0	t	2
279	11	999999 999	9	t	3
280	11	123456789 987654321	9	t	3
281	11	1000000007 1000000009	1	t	3
282	11	2147483647 2147483646	1	t	3
283	11	2 2147483646	2	t	3
284	11	1000000000 999999999	1	t	3
285	11	999999937 999999938	1	t	3
286	11	536870912 268435456	268435456	t	3
287	11	1073741824 536870912	536870912	t	3
288	11	1000000000 500000000	500000000	t	3
289	12	listen\\nsilent	YES	f	1
290	12	hello\\nworld	NO	t	1
291	12	abc\\ncba	YES	t	1
292	12	test\\ntset	YES	t	1
293	12	a\\na	YES	t	2
294	12	a\\nb	NO	t	2
295	12	ab\\nba	YES	t	2
296	12	ab\\nab	YES	t	2
297	12	ab\\nac	NO	t	2
298	12	triangle\\nintegral	YES	t	2
299	12	angered\\nenraged	YES	t	2
300	12	apple\\npapel	YES	t	2
301	12	car\\narc	YES	t	2
302	12	cat\\nact	YES	t	2
303	12	dog\\ngod	YES	t	2
304	12	evil\\nvile	YES	t	2
305	12	flow\\nwolf	YES	t	3
306	12	night\\nthing	YES	t	3
307	12	peach\\ncheap	YES	t	3
308	12	earth\\nheart	YES	t	3
309	12	abcdefgh\\nhgfedcba	YES	t	3
310	12	aaaaaaaaaa\\nbbbbbbbbbb	NO	t	3
311	12	aaaaaaaaaa\\naaaaaaaaaa	YES	t	3
312	12	aaaaaaaaab\\naaaaaaaaac	NO	t	3
313	12	12345\\n54321	YES	t	3
314	12	aab\\nabb	NO	t	3
315	12	aaaabbbb\\naaaabbbc	NO	t	3
316	12	aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\\naaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa	YES	t	3
317	12	aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\\naaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab	NO	t	3
318	14	5 2 8	2	f	1
319	14	-3 0 3	-3	t	1
320	14	7 7 7	7	t	1
321	14	10 -5 0	-5	t	1
322	14	1 2 3	1	t	1
323	14	3 2 1	1	t	1
324	14	2 1 3	1	t	1
325	14	-1 -2 -3	-3	t	1
326	14	0 0 0	0	t	1
327	14	100 200 50	50	t	1
328	14	-100 -50 -200	-200	t	1
329	14	999 888 777	777	t	1
330	14	42 42 21	21	t	1
331	14	0 -100 100	-100	t	1
332	14	5 -5 0	-5	t	1
333	14	123 456 789	123	t	1
334	14	-999 0 999	-999	t	1
335	14	2147483647 0 -2147483648	-2147483648	t	2
336	14	1000000 2000000 3000000	1000000	t	2
337	14	-1000000 -2000000 -3000000	-3000000	t	2
338	14	777777 666666 555555	555555	t	2
339	14	1 1 2	1	t	2
340	14	2 2 1	1	t	2
341	14	3 1 1	1	t	2
342	14	100 100 100	100	t	2
343	14	-100 -100 -100	-100	t	2
344	14	0 1 -1	-1	t	3
345	14	2147483647 2147483646 2147483645	2147483645	t	3
346	14	-2147483648 -2147483647 -2147483646	-2147483648	t	3
347	15	5	15	f	1
348	15	10	55	t	1
349	15	1	1	t	1
350	15	100	5050	t	1
351	15	2	3	t	1
352	15	3	6	t	1
353	15	4	10	t	1
354	15	6	21	t	1
355	15	7	28	t	1
356	15	8	36	t	1
357	15	9	45	t	1
358	15	20	210	t	2
359	15	30	465	t	2
360	15	50	1275	t	2
361	15	75	2850	t	2
362	15	99	4950	t	2
363	15	200	20100	t	2
364	15	300	45150	t	2
365	15	400	80200	t	2
366	15	500	125250	t	2
367	15	600	180300	t	3
368	15	700	245350	t	3
369	15	800	320400	t	3
370	15	900	405450	t	3
371	15	1000	500500	t	3
372	15	250	31375	t	3
373	15	350	61425	t	3
374	15	450	101475	t	3
375	15	550	151525	t	3
376	16	123	321	f	1
377	16	-456	-654	t	1
378	16	1000	1	t	1
379	16	0	0	t	1
380	16	1	1	t	1
381	16	-1	-1	t	1
382	16	10	1	t	1
383	16	-10	-1	t	1
384	16	101	101	t	1
385	16	-101	-101	t	1
386	16	1234	4321	t	1
387	16	-1234	-4321	t	1
388	16	1200	21	t	2
389	16	-1200	-21	t	2
390	16	10000	1	t	2
391	16	-10000	-1	t	2
392	16	99999	99999	t	2
393	16	-99999	-99999	t	2
394	16	123456	654321	t	2
395	16	-123456	-654321	t	2
396	16	1000000	1	t	3
397	16	-1000000	-1	t	3
398	16	2147483647	7463847412	t	3
399	16	-2147483648	-8463847412	t	3
400	16	987654321	123456789	t	3
401	16	-987654321	-123456789	t	3
402	16	1234567890	987654321	t	3
403	16	-1234567890	-987654321	t	3
404	16	1000000007	7000000001	t	3
405	17	12	6	f	1
406	17	1	1	t	1
407	17	17	2	t	1
408	17	36	9	t	1
409	17	2	2	t	1
410	17	3	2	t	1
411	17	4	3	t	1
412	17	5	2	t	1
413	17	6	4	t	1
414	17	7	2	t	1
415	17	8	4	t	1
416	17	9	3	t	2
417	17	10	4	t	2
418	17	24	8	t	2
419	17	30	8	t	2
420	17	48	10	t	2
421	17	60	12	t	2
422	17	72	12	t	2
423	17	84	12	t	2
424	17	96	12	t	2
425	17	100	9	t	3
426	17	144	15	t	3
427	17	180	18	t	3
428	17	240	20	t	3
429	17	360	24	t	3
430	17	720	30	t	3
431	17	840	32	t	3
432	17	1000	16	t	3
433	17	10000	25	t	3
434	17	100000	36	t	3
435	17	500000	42	t	3
436	17	999983	2	t	3
437	18	10	30	f	1
438	18	5	6	t	1
439	18	1	0	t	1
440	18	20	110	t	1
441	18	2	2	t	1
442	18	3	2	t	1
443	18	4	6	t	1
444	18	6	12	t	1
445	18	7	12	t	1
446	18	8	20	t	1
447	18	9	20	t	1
448	18	11	30	t	1
449	18	12	42	t	2
450	18	15	56	t	2
451	18	25	156	t	2
452	18	30	240	t	2
453	18	40	420	t	2
454	18	50	650	t	2
455	18	75	1406	t	2
456	18	100	2550	t	2
457	18	150	5700	t	3
458	18	200	10100	t	3
459	18	250	15750	t	3
460	18	300	22650	t	3
461	18	400	40200	t	3
462	18	500	62750	t	3
463	18	750	141000	t	3
464	18	1000	250500	t	3
465	18	999	249500	t	3
466	19	8	YES	f	1
467	19	6	NO	t	1
468	19	1	YES	t	1
469	19	256	YES	t	1
470	19	2	YES	t	1
471	19	4	YES	t	1
472	19	16	YES	t	1
473	19	32	YES	t	1
474	19	64	YES	t	1
475	19	128	YES	t	1
476	19	512	YES	t	2
477	19	1024	YES	t	2
478	19	3	NO	t	2
479	19	5	NO	t	2
480	19	7	NO	t	2
481	19	9	NO	t	2
482	19	10	NO	t	2
483	19	12	NO	t	2
484	19	14	NO	t	2
485	19	15	NO	t	2
486	19	18	NO	t	2
487	19	24	NO	t	2
488	19	28	NO	t	2
489	19	31	NO	t	3
490	19	33	NO	t	3
491	19	2048	YES	t	3
492	19	4096	YES	t	3
493	19	8192	YES	t	3
494	19	16384	YES	t	3
495	19	32768	YES	t	3
496	19	65536	YES	t	3
497	19	131072	YES	t	3
498	19	262144	YES	t	3
499	19	524288	YES	t	3
500	19	1048576	YES	t	3
501	19	2097152	YES	t	3
502	19	4194304	YES	t	3
503	19	8388608	YES	t	3
504	19	16777216	YES	t	3
505	19	33554432	YES	t	3
506	19	67108864	YES	t	3
507	19	134217728	YES	t	3
508	19	268435456	YES	t	3
509	19	536870912	YES	t	3
510	20	5 2	10	f	1
511	20	0 0	1	t	1
512	20	7 3	35	t	1
513	20	10 5	252	t	1
514	20	1 0	1	t	1
515	20	1 1	1	t	1
516	20	2 0	1	t	1
517	20	2 1	2	t	1
518	20	2 2	1	t	1
519	20	3 1	3	t	1
520	20	3 2	3	t	1
521	20	4 2	6	t	2
522	20	6 3	20	t	2
523	20	8 4	70	t	2
524	20	9 2	36	t	2
525	20	9 7	36	t	2
526	20	10 0	1	t	2
527	20	10 10	1	t	2
528	20	11 5	462	t	2
529	20	12 6	924	t	2
530	20	13 4	715	t	3
531	20	14 7	3432	t	3
532	20	15 8	6435	t	3
533	20	16 9	11440	t	3
534	20	17 10	19448	t	3
535	20	18 9	48620	t	3
536	20	19 5	11628	t	3
537	20	20 10	184756	t	3
538	20	20 0	1	t	3
539	20	20 20	1	t	3
540	21	10	25	f	1
541	21	5	9	t	1
542	21	1	1	t	1
543	21	9	25	t	1
544	21	2	1	t	1
545	21	3	4	t	1
546	21	4	4	t	1
547	21	6	9	t	1
548	21	7	16	t	1
549	21	8	16	t	1
550	21	11	36	t	1
551	21	12	36	t	1
552	21	13	49	t	2
553	21	15	64	t	2
554	21	20	100	t	2
555	21	25	169	t	2
556	21	30	225	t	2
557	21	35	324	t	2
558	21	40	400	t	2
559	21	45	529	t	2
560	21	50	625	t	3
561	21	60	900	t	3
562	21	70	1225	t	3
563	21	80	1600	t	3
564	21	90	2025	t	3
565	21	100	2500	t	3
566	21	150	5625	t	3
567	21	200	10000	t	3
568	21	250	15625	t	3
569	21	300	22500	t	3
570	21	400	40000	t	3
571	21	500	62500	t	3
572	22	3 4 5	YES	f	1
573	22	1 2 3	NO	t	1
574	22	5 5 5	YES	t	1
575	22	10 1 1	NO	t	1
576	22	2 3 4	YES	t	1
577	22	6 8 10	YES	t	1
578	22	7 24 25	YES	t	1
579	22	1 1 2	NO	t	1
580	22	2 2 1	YES	t	1
581	22	100 100 100	YES	t	1
582	22	1 100 100	YES	t	1
583	22	2 3 6	NO	t	2
584	22	5 12 13	YES	t	2
585	22	8 15 17	YES	t	2
586	22	9 40 41	YES	t	2
587	22	20 21 29	YES	t	2
588	22	50 50 99	YES	t	2
589	22	50 50 100	NO	t	2
590	22	100 200 300	NO	t	2
591	22	150 200 100	YES	t	2
592	22	500 500 999	YES	t	3
593	22	500 500 1000	NO	t	3
594	22	999 999 1997	YES	t	3
595	22	999 999 1998	NO	t	3
596	22	1000 1000 1000	YES	t	3
597	22	1 1 1	YES	t	3
598	22	1000 1 1000	YES	t	3
599	22	1000 500 501	YES	t	3
600	22	1000 500 500	NO	t	3
601	22	999 998 1997	YES	t	3
602	23	12345	5	f	1
603	23	987	9	t	1
604	23	1000	1	t	1
605	23	9	9	t	1
606	23	1	1	t	1
607	23	10	1	t	1
608	23	11	1	t	1
609	23	99	9	t	1
610	23	101	1	t	1
611	23	909	9	t	1
612	23	123	3	t	1
613	23	321	3	t	1
614	23	456	6	t	1
615	23	789	9	t	1
616	23	555	5	t	2
617	23	777	7	t	2
618	23	888	8	t	2
619	23	1000000	1	t	2
620	23	9999999	9	t	2
621	23	123456789	9	t	2
622	23	987654321	9	t	2
623	23	102030405	5	t	2
624	23	505050505	5	t	2
625	23	909090909	9	t	2
626	23	2147483647	8	t	3
627	23	1000000000	1	t	3
628	23	999999999	9	t	3
629	23	1234567890	9	t	3
630	23	9876543210	9	t	3
631	23	5555555555	5	t	3
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, email, password_hash, created_at, elo, best_elo, wins, losses, games_played, title, draws, is_online, last_seen, onboarding_completed, preferred_language, experience_level, current_streak, is_premium, premium_until) FROM stdin;
2	MISTIK	e.kraeva@bda.com	$2b$12$d57eqQf9CNb/..eImZ7R4O9dBPNa.qOp9DElweBmQAJ6kaqdOvDzS	2025-11-04 19:02:16.162693	1000	1000	0	0	0	Новичок	0	f	2025-12-22 13:41:12.489756	f	python	novice	0	f	\N
4	jsgjwg	ovesik07-0775@mail.ru	$2b$12$zQYDrOtYStgdtXMx3Suo7eKaMYJp1W1Br5GseX6ZvRuIfIMT4FGA.	2026-01-15 08:51:16.850329	1000	1000	0	0	0	Новичок	0	f	2026-01-15 08:51:17.355697	f	python	novice	0	f	\N
7	kkkk	k@mail.ru	$2b$12$kKrlyGummvB3hRGozZMINeVRJVcFS.1Ckwv9nolxGIw851m3/bjcy	2026-01-19 12:37:37.314075	995	1059	5	6	12	Новичок	1	f	2026-02-01 22:27:05.640986	f	python	novice	0	f	\N
5	dnfefjh	leradavidova111@yandex.com	$2b$12$xj2jEEord8IRd1.uBLadiuzKp3ePfGUVN.MWZNOCb4vEJFO2ut78O	2026-01-15 08:52:22.79635	1000	1000	0	0	0	Новичок	0	f	2026-01-15 10:33:16.309086	f	python	novice	0	f	\N
9	oooooo	1@mail.ru	$2b$12$TjQD9F4v5jz83nat3/tZwegB3ocFJv6cjbD3lv05oL55CGklL35Jm	2026-02-01 22:26:37.947734	1017	1017	1	0	1	Новичок	0	f	2026-02-01 22:27:08.438019	f	python	novice	0	f	\N
6	popa	egor@gmail.com	$2b$12$fDdxlX7u4qKGCyg6jrChtuH3AzCWemltoGIBxk7fsEwSn7pbAjdg6	2026-01-15 10:33:08.34786	1000	1000	0	0	0	Новичок	0	f	2026-01-15 11:02:21.537714	f	python	novice	0	f	\N
8	mmmkkk	e@mail.ru	$2b$12$gmVFHUuNNEWvTiX/uXfsZeleGwcbUeE3yR3BoIx3eQuSLtTmIRaZ2	2026-02-01 22:25:38.913862	1000	1000	0	0	0	Новичок	0	f	2026-02-01 22:25:39.154518	f	python	novice	0	f	\N
1	mistik	guzarevicvlad47@mail.ru	$2b$12$Vj0H6uUD8r6ldUx1tiy.HeGCcsrLDAzT6CdlS7tV.QCGPA7GkhXk.	2025-11-04 18:40:37.778167	1129	2200	76	59	138	Мастер алгоритмов	1	t	2026-04-22 21:42:18.521342	t	python	novice	2	t	2026-04-09 21:53:40.452121
10	proplayer	admin@mail.ru	$2b$12$GvKgf0na0aRxLOHvxiT59e07HxOr54v0aCBSvKFnLe1iYZAsrZTlC	2026-03-10 22:05:52.221987	1044	1044	2	0	2	Новичок	0	f	2026-03-10 23:22:01.500031	t	python	novice	2	t	2026-04-09 22:45:58.786896
3	kkkkk	ktyf79@mail.ru	$2b$12$2DXmrzoHBtXgmSoa4SjUaeFcOO8PWeRoPjBartX1O49/4l0FeVWta	2025-11-05 23:46:15.407721	989	1000	0	1	1	Новичок	0	f	2026-04-08 22:09:17.83384	t	python	novice	0	f	\N
12	test01	admin01@mail.ru	$2b$12$/BGQUGTrjj1gEjYTQXWuneGKM/fFPXBYhAOnYXZ0lyrHJ09GOLhgm	2026-04-22 20:30:25.991687	989	1000	0	1	1	Новичок	0	t	2026-04-22 21:42:32.628701	t	python	novice	0	f	\N
\.


--
-- Name: attempts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.attempts_id_seq', 67, true);


--
-- Name: match_results_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.match_results_id_seq', 19, true);


--
-- Name: matches_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.matches_id_seq', 32, true);


--
-- Name: matchmaking_queue_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.matchmaking_queue_id_seq', 109, true);


--
-- Name: rating_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.rating_id_seq', 1, false);


--
-- Name: tasks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.tasks_id_seq', 23, true);


--
-- Name: test_cases_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.test_cases_id_seq', 631, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 12, true);


--
-- Name: attempts attempts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attempts
    ADD CONSTRAINT attempts_pkey PRIMARY KEY (id);


--
-- Name: match_results match_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_results
    ADD CONSTRAINT match_results_pkey PRIMARY KEY (id);


--
-- Name: matches matches_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matches
    ADD CONSTRAINT matches_pkey PRIMARY KEY (id);


--
-- Name: matchmaking_queue matchmaking_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matchmaking_queue
    ADD CONSTRAINT matchmaking_queue_pkey PRIMARY KEY (id);


--
-- Name: rating rating_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rating
    ADD CONSTRAINT rating_pkey PRIMARY KEY (id);


--
-- Name: rating rating_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rating
    ADD CONSTRAINT rating_user_id_key UNIQUE (user_id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- Name: test_cases test_cases_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_cases
    ADD CONSTRAINT test_cases_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_matches_active_opponent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_matches_active_opponent ON public.matches USING btree (opponent_id) WHERE (result IS NULL);


--
-- Name: idx_matches_active_user; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_matches_active_user ON public.matches USING btree (user_id) WHERE (result IS NULL);


--
-- Name: idx_matches_played_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_matches_played_at ON public.matches USING btree (played_at);


--
-- Name: idx_matches_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_matches_user_id ON public.matches USING btree (user_id);


--
-- Name: idx_matchmaking_queue_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_matchmaking_queue_status ON public.matchmaking_queue USING btree (status) WHERE ((status)::text = 'searching'::text);


--
-- Name: idx_rating_points; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_rating_points ON public.rating USING btree (total_points DESC);


--
-- Name: idx_tasks_difficulty; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_tasks_difficulty ON public.tasks USING btree (difficulty_level);


--
-- Name: idx_users_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_username ON public.users USING btree (username);


--
-- Name: attempts attempts_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attempts
    ADD CONSTRAINT attempts_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id);


--
-- Name: attempts attempts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attempts
    ADD CONSTRAINT attempts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: match_results match_results_attempt_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_results
    ADD CONSTRAINT match_results_attempt_id_fkey FOREIGN KEY (attempt_id) REFERENCES public.attempts(id);


--
-- Name: match_results match_results_match_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_results
    ADD CONSTRAINT match_results_match_id_fkey FOREIGN KEY (match_id) REFERENCES public.matches(id);


--
-- Name: match_results match_results_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_results
    ADD CONSTRAINT match_results_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: matches matches_opponent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matches
    ADD CONSTRAINT matches_opponent_id_fkey FOREIGN KEY (opponent_id) REFERENCES public.users(id);


--
-- Name: matches matches_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matches
    ADD CONSTRAINT matches_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id);


--
-- Name: matches matches_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matches
    ADD CONSTRAINT matches_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: matchmaking_queue matchmaking_queue_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matchmaking_queue
    ADD CONSTRAINT matchmaking_queue_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id);


--
-- Name: matchmaking_queue matchmaking_queue_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matchmaking_queue
    ADD CONSTRAINT matchmaking_queue_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: rating rating_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rating
    ADD CONSTRAINT rating_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: test_cases test_cases_task_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_cases
    ADD CONSTRAINT test_cases_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.tasks(id) ON DELETE CASCADE;


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

\unrestrict TqlS2VqAojMWtmdXv1ZwoIO1i8ayyVego03OrTS9y6Q1OBlwaeLnD2yhhhUjVkZ

