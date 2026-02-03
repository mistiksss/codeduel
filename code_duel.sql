--
-- PostgreSQL database dump
--

\restrict kyy4fADw0xa8hYKNqfKtfJqx320KnrvFGdWdrb9q0L0j0cnUXkFZDhbJ2yy30v0

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
    CONSTRAINT matches_result_check CHECK (((result)::text = ANY ((ARRAY['win'::character varying, 'loss'::character varying, 'draw'::character varying])::text[])))
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
    CONSTRAINT tasks_difficulty_level_check CHECK (((difficulty_level)::text = ANY ((ARRAY['легкая'::character varying, 'средняя'::character varying, 'сложная'::character varying])::text[])))
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
    last_seen timestamp without time zone DEFAULT CURRENT_TIMESTAMP
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
1	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	error	0	\N	0	0	0	No test cases found for this task	2025-12-16 05:46:14.27272
2	1	1	const readline = require('readline');\n\nasync function main() {\n    const rl = readline.createInterface({\n        input: process.stdin,\n        output: process.stdout,\n        terminal: false\n    });\n    \n    const lines = [];\n    for await (const line of rl) {\n        lines.push(line);\n    }\n    \n    // Ваш код здесь\n    const n = parseInt(lines[0]);\n    console.log(n * 2);\n}\n\nif (require.main === module) {\n    main().catch(console.error);\n}	javascript	error	0	\N	0	0	0	No test cases found for this task	2025-12-16 05:47:32.915968
3	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	runtime_error	0.05424783229827881	\N	0	50	0	\N	2025-12-16 06:08:53.139048
4	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	runtime_error	0.051023335456848146	\N	0	50	0	[{"test_id": 1, "passed": false, "status": "runtime_error"}, {"test_id": 2, "passed": false, "status": "runtime_error"}, {"test_id": 3, "passed": false, "status": "runtime_error"}, {"test_id": 4, "passed": false, "status": "runtime_error"}, {"test_id": 5, "passed": false, "status": "runtime_error"}, {"test_id": 6, "passed": false, "status": "runtime_error"}, {"test_id": 7, "passed": false, "status": "runtime_error"}, {"test_id": 8, "passed": false, "status": "runtime_error"}, {"test_id": 9, "passed": false, "status": "runtime_error"}, {"test_id": 10, "passed": false, "status": "runtime_error"}, {"test_id": 11, "passed": false, "status": "runtime_error"}, {"test_id": 12, "passed": false, "status": "runtime_error"}, {"test_id": 13, "passed": false, "status": "runtime_error"}, {"test_id": 14, "passed": false, "status": "runtime_error"}, {"test_id": 15, "passed": false, "status": "runtime_error"}, {"test_id": 16, "passed": false, "status": "runtime_error"}, {"test_id": 17, "passed": false, "status": "runtime_error"}, {"test_id": 18, "passed": false, "status": "runtime_error"}, {"test_id": 19, "passed": false, "status": "runtime_error"}, {"test_id": 20, "passed": false, "status": "runtime_error"}, {"test_id": 21, "passed": false, "status": "runtime_error"}, {"test_id": 22, "passed": false, "status": "runtime_error"}, {"test_id": 23, "passed": false, "status": "runtime_error"}, {"test_id": 24, "passed": false, "status": "runtime_error"}, {"test_id": 25, "passed": false, "status": "runtime_error"}, {"test_id": 26, "passed": false, "status": "runtime_error"}, {"test_id": 27, "passed": false, "status": "runtime_error"}, {"test_id": 28, "passed": false, "status": "runtime_error"}, {"test_id": 29, "passed": false, "status": "runtime_error"}, {"test_id": 30, "passed": false, "status": "runtime_error"}, {"test_id": 31, "passed": false, "status": "runtime_error"}, {"test_id": 32, "passed": false, "status": "runtime_error"}, {"test_id": 33, "passed": false, "status": "runtime_error"}, {"test_id": 34, "passed": false, "status": "runtime_error"}, {"test_id": 35, "passed": false, "status": "runtime_error"}, {"test_id": 36, "passed": false, "status": "runtime_error"}, {"test_id": 37, "passed": false, "status": "runtime_error"}, {"test_id": 38, "passed": false, "status": "runtime_error"}, {"test_id": 39, "passed": false, "status": "runtime_error"}, {"test_id": 40, "passed": false, "status": "runtime_error"}, {"test_id": 41, "passed": false, "status": "runtime_error"}, {"test_id": 42, "passed": false, "status": "runtime_error"}, {"test_id": 43, "passed": false, "status": "runtime_error"}, {"test_id": 44, "passed": false, "status": "runtime_error"}, {"test_id": 45, "passed": false, "status": "runtime_error"}, {"test_id": 46, "passed": false, "status": "runtime_error"}, {"test_id": 47, "passed": false, "status": "runtime_error"}, {"test_id": 48, "passed": false, "status": "runtime_error"}, {"test_id": 49, "passed": false, "status": "runtime_error"}, {"test_id": 50, "passed": false, "status": "runtime_error"}]	2025-12-16 06:34:57.003283
5	1	1	def f(d):\n    c = 0\n    for s in d:\n        a = True\n        for g in s[1:]:\n            if g != 5:\n                a = False\n                break\n        if a:\n            c += 1\n    return c / len(d) if d else 0	python	wrong_answer	0.02987395763397217	\N	0	50	0	[{"test_id": 1, "passed": false, "status": "wrong_answer"}, {"test_id": 2, "passed": false, "status": "wrong_answer"}, {"test_id": 3, "passed": false, "status": "wrong_answer"}, {"test_id": 4, "passed": false, "status": "wrong_answer"}, {"test_id": 5, "passed": false, "status": "wrong_answer"}, {"test_id": 6, "passed": false, "status": "wrong_answer"}, {"test_id": 7, "passed": false, "status": "wrong_answer"}, {"test_id": 8, "passed": false, "status": "wrong_answer"}, {"test_id": 9, "passed": false, "status": "wrong_answer"}, {"test_id": 10, "passed": false, "status": "wrong_answer"}, {"test_id": 11, "passed": false, "status": "wrong_answer"}, {"test_id": 12, "passed": false, "status": "wrong_answer"}, {"test_id": 13, "passed": false, "status": "wrong_answer"}, {"test_id": 14, "passed": false, "status": "wrong_answer"}, {"test_id": 15, "passed": false, "status": "wrong_answer"}, {"test_id": 16, "passed": false, "status": "wrong_answer"}, {"test_id": 17, "passed": false, "status": "wrong_answer"}, {"test_id": 18, "passed": false, "status": "wrong_answer"}, {"test_id": 19, "passed": false, "status": "wrong_answer"}, {"test_id": 20, "passed": false, "status": "wrong_answer"}, {"test_id": 21, "passed": false, "status": "wrong_answer"}, {"test_id": 22, "passed": false, "status": "wrong_answer"}, {"test_id": 23, "passed": false, "status": "wrong_answer"}, {"test_id": 24, "passed": false, "status": "wrong_answer"}, {"test_id": 25, "passed": false, "status": "wrong_answer"}, {"test_id": 26, "passed": false, "status": "wrong_answer"}, {"test_id": 27, "passed": false, "status": "wrong_answer"}, {"test_id": 28, "passed": false, "status": "wrong_answer"}, {"test_id": 29, "passed": false, "status": "wrong_answer"}, {"test_id": 30, "passed": false, "status": "wrong_answer"}, {"test_id": 31, "passed": false, "status": "wrong_answer"}, {"test_id": 32, "passed": false, "status": "wrong_answer"}, {"test_id": 33, "passed": false, "status": "wrong_answer"}, {"test_id": 34, "passed": false, "status": "wrong_answer"}, {"test_id": 35, "passed": false, "status": "wrong_answer"}, {"test_id": 36, "passed": false, "status": "wrong_answer"}, {"test_id": 37, "passed": false, "status": "wrong_answer"}, {"test_id": 38, "passed": false, "status": "wrong_answer"}, {"test_id": 39, "passed": false, "status": "wrong_answer"}, {"test_id": 40, "passed": false, "status": "wrong_answer"}, {"test_id": 41, "passed": false, "status": "wrong_answer"}, {"test_id": 42, "passed": false, "status": "wrong_answer"}, {"test_id": 43, "passed": false, "status": "wrong_answer"}, {"test_id": 44, "passed": false, "status": "wrong_answer"}, {"test_id": 45, "passed": false, "status": "wrong_answer"}, {"test_id": 46, "passed": false, "status": "wrong_answer"}, {"test_id": 47, "passed": false, "status": "wrong_answer"}, {"test_id": 48, "passed": false, "status": "wrong_answer"}, {"test_id": 49, "passed": false, "status": "wrong_answer"}, {"test_id": 50, "passed": false, "status": "wrong_answer"}]	2025-12-16 06:36:29.458625
6	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	runtime_error	0.050701475143432616	\N	0	50	0	[{"test_id": 1, "passed": false, "status": "runtime_error"}, {"test_id": 2, "passed": false, "status": "runtime_error"}, {"test_id": 3, "passed": false, "status": "runtime_error"}, {"test_id": 4, "passed": false, "status": "runtime_error"}, {"test_id": 5, "passed": false, "status": "runtime_error"}, {"test_id": 6, "passed": false, "status": "runtime_error"}, {"test_id": 7, "passed": false, "status": "runtime_error"}, {"test_id": 8, "passed": false, "status": "runtime_error"}, {"test_id": 9, "passed": false, "status": "runtime_error"}, {"test_id": 10, "passed": false, "status": "runtime_error"}, {"test_id": 11, "passed": false, "status": "runtime_error"}, {"test_id": 12, "passed": false, "status": "runtime_error"}, {"test_id": 13, "passed": false, "status": "runtime_error"}, {"test_id": 14, "passed": false, "status": "runtime_error"}, {"test_id": 15, "passed": false, "status": "runtime_error"}, {"test_id": 16, "passed": false, "status": "runtime_error"}, {"test_id": 17, "passed": false, "status": "runtime_error"}, {"test_id": 18, "passed": false, "status": "runtime_error"}, {"test_id": 19, "passed": false, "status": "runtime_error"}, {"test_id": 20, "passed": false, "status": "runtime_error"}, {"test_id": 21, "passed": false, "status": "runtime_error"}, {"test_id": 22, "passed": false, "status": "runtime_error"}, {"test_id": 23, "passed": false, "status": "runtime_error"}, {"test_id": 24, "passed": false, "status": "runtime_error"}, {"test_id": 25, "passed": false, "status": "runtime_error"}, {"test_id": 26, "passed": false, "status": "runtime_error"}, {"test_id": 27, "passed": false, "status": "runtime_error"}, {"test_id": 28, "passed": false, "status": "runtime_error"}, {"test_id": 29, "passed": false, "status": "runtime_error"}, {"test_id": 30, "passed": false, "status": "runtime_error"}, {"test_id": 31, "passed": false, "status": "runtime_error"}, {"test_id": 32, "passed": false, "status": "runtime_error"}, {"test_id": 33, "passed": false, "status": "runtime_error"}, {"test_id": 34, "passed": false, "status": "runtime_error"}, {"test_id": 35, "passed": false, "status": "runtime_error"}, {"test_id": 36, "passed": false, "status": "runtime_error"}, {"test_id": 37, "passed": false, "status": "runtime_error"}, {"test_id": 38, "passed": false, "status": "runtime_error"}, {"test_id": 39, "passed": false, "status": "runtime_error"}, {"test_id": 40, "passed": false, "status": "runtime_error"}, {"test_id": 41, "passed": false, "status": "runtime_error"}, {"test_id": 42, "passed": false, "status": "runtime_error"}, {"test_id": 43, "passed": false, "status": "runtime_error"}, {"test_id": 44, "passed": false, "status": "runtime_error"}, {"test_id": 45, "passed": false, "status": "runtime_error"}, {"test_id": 46, "passed": false, "status": "runtime_error"}, {"test_id": 47, "passed": false, "status": "runtime_error"}, {"test_id": 48, "passed": false, "status": "runtime_error"}, {"test_id": 49, "passed": false, "status": "runtime_error"}, {"test_id": 50, "passed": false, "status": "runtime_error"}]	2025-12-16 06:53:28.508194
7	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	runtime_error	0.05064337253570557	\N	0	50	0	[{"test_id": 1, "passed": false, "status": "runtime_error"}, {"test_id": 2, "passed": false, "status": "runtime_error"}, {"test_id": 3, "passed": false, "status": "runtime_error"}, {"test_id": 4, "passed": false, "status": "runtime_error"}, {"test_id": 5, "passed": false, "status": "runtime_error"}, {"test_id": 6, "passed": false, "status": "runtime_error"}, {"test_id": 7, "passed": false, "status": "runtime_error"}, {"test_id": 8, "passed": false, "status": "runtime_error"}, {"test_id": 9, "passed": false, "status": "runtime_error"}, {"test_id": 10, "passed": false, "status": "runtime_error"}, {"test_id": 11, "passed": false, "status": "runtime_error"}, {"test_id": 12, "passed": false, "status": "runtime_error"}, {"test_id": 13, "passed": false, "status": "runtime_error"}, {"test_id": 14, "passed": false, "status": "runtime_error"}, {"test_id": 15, "passed": false, "status": "runtime_error"}, {"test_id": 16, "passed": false, "status": "runtime_error"}, {"test_id": 17, "passed": false, "status": "runtime_error"}, {"test_id": 18, "passed": false, "status": "runtime_error"}, {"test_id": 19, "passed": false, "status": "runtime_error"}, {"test_id": 20, "passed": false, "status": "runtime_error"}, {"test_id": 21, "passed": false, "status": "runtime_error"}, {"test_id": 22, "passed": false, "status": "runtime_error"}, {"test_id": 23, "passed": false, "status": "runtime_error"}, {"test_id": 24, "passed": false, "status": "runtime_error"}, {"test_id": 25, "passed": false, "status": "runtime_error"}, {"test_id": 26, "passed": false, "status": "runtime_error"}, {"test_id": 27, "passed": false, "status": "runtime_error"}, {"test_id": 28, "passed": false, "status": "runtime_error"}, {"test_id": 29, "passed": false, "status": "runtime_error"}, {"test_id": 30, "passed": false, "status": "runtime_error"}, {"test_id": 31, "passed": false, "status": "runtime_error"}, {"test_id": 32, "passed": false, "status": "runtime_error"}, {"test_id": 33, "passed": false, "status": "runtime_error"}, {"test_id": 34, "passed": false, "status": "runtime_error"}, {"test_id": 35, "passed": false, "status": "runtime_error"}, {"test_id": 36, "passed": false, "status": "runtime_error"}, {"test_id": 37, "passed": false, "status": "runtime_error"}, {"test_id": 38, "passed": false, "status": "runtime_error"}, {"test_id": 39, "passed": false, "status": "runtime_error"}, {"test_id": 40, "passed": false, "status": "runtime_error"}, {"test_id": 41, "passed": false, "status": "runtime_error"}, {"test_id": 42, "passed": false, "status": "runtime_error"}, {"test_id": 43, "passed": false, "status": "runtime_error"}, {"test_id": 44, "passed": false, "status": "runtime_error"}, {"test_id": 45, "passed": false, "status": "runtime_error"}, {"test_id": 46, "passed": false, "status": "runtime_error"}, {"test_id": 47, "passed": false, "status": "runtime_error"}, {"test_id": 48, "passed": false, "status": "runtime_error"}, {"test_id": 49, "passed": false, "status": "runtime_error"}, {"test_id": 50, "passed": false, "status": "runtime_error"}]	2025-12-16 06:54:31.298139
8	1	1	def f(d):\n    c = 0\n    for s in d:\n        a = True\n        for g in s[1:]:\n            if g != 5:\n                a = False\n                break\n        if a:\n            c += 1\n    return c / len(d) if d else 0\nprint(f(input()))	python	wrong_answer	0.03241807460784912	\N	13	50	31	[{"test_id": 1, "passed": true, "status": "passed"}, {"test_id": 2, "passed": false, "status": "wrong_answer"}, {"test_id": 3, "passed": false, "status": "wrong_answer"}, {"test_id": 4, "passed": true, "status": "passed"}, {"test_id": 5, "passed": false, "status": "wrong_answer"}, {"test_id": 6, "passed": false, "status": "wrong_answer"}, {"test_id": 7, "passed": true, "status": "passed"}, {"test_id": 8, "passed": false, "status": "wrong_answer"}, {"test_id": 9, "passed": false, "status": "wrong_answer"}, {"test_id": 10, "passed": false, "status": "wrong_answer"}, {"test_id": 11, "passed": true, "status": "passed"}, {"test_id": 12, "passed": false, "status": "wrong_answer"}, {"test_id": 13, "passed": false, "status": "wrong_answer"}, {"test_id": 14, "passed": true, "status": "passed"}, {"test_id": 15, "passed": true, "status": "passed"}, {"test_id": 16, "passed": false, "status": "wrong_answer"}, {"test_id": 17, "passed": true, "status": "passed"}, {"test_id": 18, "passed": false, "status": "wrong_answer"}, {"test_id": 19, "passed": false, "status": "wrong_answer"}, {"test_id": 20, "passed": false, "status": "wrong_answer"}, {"test_id": 21, "passed": false, "status": "wrong_answer"}, {"test_id": 22, "passed": false, "status": "wrong_answer"}, {"test_id": 23, "passed": false, "status": "wrong_answer"}, {"test_id": 24, "passed": false, "status": "wrong_answer"}, {"test_id": 25, "passed": false, "status": "wrong_answer"}, {"test_id": 26, "passed": false, "status": "wrong_answer"}, {"test_id": 27, "passed": false, "status": "wrong_answer"}, {"test_id": 28, "passed": false, "status": "wrong_answer"}, {"test_id": 29, "passed": false, "status": "wrong_answer"}, {"test_id": 30, "passed": true, "status": "passed"}, {"test_id": 31, "passed": false, "status": "wrong_answer"}, {"test_id": 32, "passed": false, "status": "wrong_answer"}, {"test_id": 33, "passed": false, "status": "wrong_answer"}, {"test_id": 34, "passed": true, "status": "passed"}, {"test_id": 35, "passed": true, "status": "passed"}, {"test_id": 36, "passed": false, "status": "wrong_answer"}, {"test_id": 37, "passed": false, "status": "wrong_answer"}, {"test_id": 38, "passed": false, "status": "wrong_answer"}, {"test_id": 39, "passed": false, "status": "wrong_answer"}, {"test_id": 40, "passed": true, "status": "passed"}, {"test_id": 41, "passed": false, "status": "wrong_answer"}, {"test_id": 42, "passed": false, "status": "wrong_answer"}, {"test_id": 43, "passed": true, "status": "passed"}, {"test_id": 44, "passed": false, "status": "wrong_answer"}, {"test_id": 45, "passed": false, "status": "wrong_answer"}, {"test_id": 46, "passed": false, "status": "wrong_answer"}, {"test_id": 47, "passed": false, "status": "wrong_answer"}, {"test_id": 48, "passed": false, "status": "wrong_answer"}, {"test_id": 49, "passed": false, "status": "wrong_answer"}, {"test_id": 50, "passed": true, "status": "passed"}]	2025-12-16 07:02:52.667858
9	1	1	def f(d):\n    c = 0\n    for s in d:\n        a = True\n        for g in s[1:]:\n            if g != 5:\n                a = False\n                break\n        if a:\n            c += 1\n    return c / len(d) if d else 0\nprint(f(input()))	python	partially_correct	0.03186095714569092	\N	13	50	31	\N	2025-12-16 07:42:52.568272
10	1	1	def f(d):\n    c = 0\n    for s in d:\n        a = True\n        for g in s[1:]:\n            if g != 5:\n                a = False\n                break\n        if a:\n            c += 1\n    return c / len(d) if d else 0\nprint(f(input()))	python	partially_correct	0.029947056770324706	\N	13	50	31	\N	2025-12-16 07:43:27.535877
11	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	runtime_error	0.09778978824615478	\N	0	50	0	\N	2025-12-16 12:35:48.333677
12	1	1	#include <iostream>\nusing namespace std;\n\nint main() {\n    // Ваш код здесь\n    int n;\n    cin >> n;\n    cout << n * 2 << endl;\n    return 0;\n}	cpp	compilation_error	0	\N	0	50	0	\N	2025-12-16 12:37:02.046461
13	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	runtime_error	0.05682997226715088	\N	0	50	0	\N	2025-12-18 05:36:35.09808
14	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	runtime_error	0.04995228767395019	\N	0	50	0	\N	2025-12-18 05:36:54.401077
15	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	runtime_error	0.053965673446655274	\N	0	50	0	\N	2025-12-18 05:36:56.132862
16	1	1	import java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner scanner = new Scanner(System.in);\n        // Ваш код здесь\n        int n = scanner.nextInt();\n        System.out.println(n * 2);\n        scanner.close();\n    }\n}	java	compilation_error	0	\N	0	50	0	\N	2026-01-01 12:24:03.114216
17	1	1	import java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner scanner = new Scanner(System.in);\n        // Ваш код здесь\n        int n = scanner.nextInt();\n        System.out.println(n * 2);\n        scanner.close();\n    }\n}Ваш\n	java	compilation_error	0	\N	0	50	0	\N	2026-01-01 12:26:02.768951
18	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()lol	python	runtime_error	0.14491149425506591	\N	0	50	0	\N	2026-01-01 12:27:41.915299
19	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()lol	python	runtime_error	0.1395000696182251	\N	0	50	0	\N	2026-01-01 12:27:57.11328
20	1	1	def main():\nlol\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	runtime_error	0.12766277313232421	\N	0	50	0	\N	2026-01-01 12:29:15.195447
21	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	runtime_error	0.09981229782104492	\N	0	50	0	\N	2026-01-01 17:36:58.570185
23	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	runtime_error	0.0987166690826416	\N	0	50	0	\N	2026-01-01 17:36:58.838552
22	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	runtime_error	0.09686102390289307	\N	0	50	0	\N	2026-01-01 17:36:58.742959
24	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	runtime_error	0.09889940738677978	\N	0	50	0	\N	2026-01-01 17:36:59.003726
25	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	runtime_error	0.0906063461303711	\N	0	50	0	\N	2026-01-01 17:40:29.751156
26	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	runtime_error	0.08980079174041748	\N	0	50	0	\N	2026-01-01 18:09:40.214377
27	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	runtime_error	0.09627849102020264	\N	0	50	0	\N	2026-01-01 21:30:37.494487
28	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	testing	\N	\N	0	0	0	\N	2026-01-02 16:29:30.680882
29	1	1	def main():\n    # Введите ваш код здесь\n    n = int(input())\n    print(n * 2)\n\nif __name__ == "__main__":\n    main()	python	wrong_answer	0	\N	0	50	0	\N	2026-01-02 16:39:58.786296
30	1	1	print(2 * int(input()))	python	runtime_error	0.08659999999999997	\N	0	50	0	Traceback (most recent call last):\n  File "C:\\Users\\E67B~1\\AppData\\Local\\Temp\\tmp3qj8dulb.py", line 1, in <module>\n    print(2 * int(input()))\n                  ~~~~~^^\n  File "<frozen codecs>", line 	2026-01-14 18:11:17.259058
31	1	1	print(2 * int(input()))	python	runtime_error	0.07922000000000001	\N	0	50	0	Traceback (most recent call last):\n  File "C:\\Users\\E67B~1\\AppData\\Local\\Temp\\tmp0creiyr5.py", line 1, in <module>\n    print(2 * int(input()))\n                  ~~~~~^^\n  File "<frozen codecs>", line 	2026-01-14 18:11:37.461897
32	1	1	print(2 * int(input()))	python	runtime_error	0.08016	\N	0	50	0	Traceback (most recent call last):\n  File "C:\\Users\\E67B~1\\AppData\\Local\\Temp\\tmppu_z2csj.py", line 1, in <module>\n    print(2 * int(input()))\n                  ~~~~~^^\n  File "<frozen codecs>", line 	2026-01-14 18:11:54.962395
33	1	1	print("ok")\nprint("ok")\nprint("ok")\nprint("ok")\nprint("ok")\nprint("ok")\nprint("ok")\nprint("ok")\nprint("ok")\nprint("ok")\n	python	wrong_answer	0.05681999999999999	\N	0	50	0		2026-01-14 18:12:15.875862
34	1	1	for i in range(1, 10000):\n    print(i)	python	wrong_answer	0.13	\N	0	50	0		2026-01-14 18:12:47.319257
35	1	1	import ast\nimport sys\n\n# Читаем данные\ndata = ast.literal_eval(sys.stdin.read())\n\n# Считаем отличников\nexcellent = sum(1 for student in data if all(grade == 5 for grade in student[1:]))\n\n# Выводим результат\nprint(excellent / len(data) if data else 0.0)	python	partially_correct	0.08344000000000001	\N	1	50	1	Traceback (most recent call last):\n  File "C:\\Users\\E67B~1\\AppData\\Local\\Temp\\tmpd4k2l62o.py", line 5, in <module>\n    data = ast.literal_eval(sys.stdin.read())\n                            ~~~~~~~~~~~	2026-01-14 18:29:37.972293
36	1	1	import ast\nimport sys\n\nraw = sys.stdin.buffer.read()\n\ntry:\n    text = raw.decode("utf-8")\nexcept UnicodeDecodeError:\n    text = raw.decode("cp1251")  # Windows fallback\n\ndata = ast.literal_eval(text)\n\nexcellent = sum(\n    1 for student in data\n    if all(grade == 5 for grade in student[1:])\n)\n\nprint(excellent / len(data) if data else 0.0)\n	python	partially_correct	0.058640000000000005	\N	48	50	124		2026-01-14 18:31:46.156762
37	1	1	import ast\nimport sys\n\n# Считываем весь ввод\ndata = ast.literal_eval(sys.stdin.read())\n\nif not data:\n    print(0.0)\n    sys.exit()\n\nexcellent_count = 0\n\nfor student in data:\n    grades = student[1:]  # оценки, без имени\n    if grades and all(grade == 5 for grade in grades):\n        excellent_count += 1\n\nresult = excellent_count / len(data)\nprint(result)\n	python	partially_correct	0.09462000000000005	\N	1	50	1	Traceback (most recent call last):\n  File "C:\\Users\\E67B~1\\AppData\\Local\\Temp\\tmp5we05hof.py", line 5, in <module>\n    data = ast.literal_eval(sys.stdin.read())\n                            ~~~~~~~~~~~	2026-01-14 18:39:21.330327
38	1	1	import ast\nimport sys\n\nraw = sys.stdin.buffer.read()\n\n# пробуем UTF-8, если не получилось — cp1251\ntry:\n    text = raw.decode("utf-8")\nexcept UnicodeDecodeError:\n    text = raw.decode("cp1251")\n\ndata = ast.literal_eval(text)\n\nif not data:\n    print("0.0")\n    exit()\n\nexcellent = 0\n\nfor student in data:\n    grades = student[1:]\n    if grades and all(g == 5 for g in grades):\n        excellent += 1\n\nratio = excellent / len(data)\n\n# округление до 3 знаков\nratio = round(ratio, 3)\n\n# формат без лишних нулей\nresult = f"{ratio:.3f}".rstrip('0').rstrip('.')\n\nif result == "0":\n    result = "0.0"\nelif result == "1":\n    result = "1.0"\n\nprint(result)\n	python	accepted	0.04739999999999999	\N	50	50	130		2026-01-14 18:50:08.056896
39	1	1	import ast\nimport sys\n\nraw = sys.stdin.buffer.read()\n\n# пробуем UTF-8, если не получилось — cp1251\ntry:\n    text = raw.decode("utf-8")\nexcept UnicodeDecodeError:\n    text = raw.decode("cp1251")\n\ndata = ast.literal_eval(text)\n\nif not data:\n    print("0.0")\n    exit()\n\nexcellent = 0\n\nfor student in data:\n    grades = student[1:]\n    if grades and all(g == 5 for g in grades):\n        excellent += 1\n\nratio = excellent / len(data)\n\n# округление до 3 знаков\nratio = round(ratio, 3)\n\n# формат без лишних нулей\nresult = f"{ratio:.3f}".rstrip('0').rstrip('.')\n\nif result == "0":\n    result = "0.0"\nelif result == "1":\n    result = "1.0"\n\nprint(result)\n	python	accepted	0.043120000000000006	\N	50	50	130		2026-01-14 19:07:49.109481
40	1	1	import sys\nimport json\nimport ast\n\ns = sys.stdin.read().strip()\n\nif not s:\n    print("0.0")\n    raise SystemExit\n\n# Сначала пробуем JSON (обычно приходит так: "[[\\"Иван\\", 5, 5]]")\ntry:\n    data = json.loads(s)\nexcept Exception:\n    # Если пришло как python-литерал: [['Иван', 5, 5]]\n    data = ast.literal_eval(s)\n\n# Если после json.loads получилось строка (двойная сериализация),\n# то распаковываем второй раз\nif isinstance(data, str):\n    try:\n        data = json.loads(data)\n    except Exception:\n        data = ast.literal_eval(data)\n\nif not data:\n    print("0.0")\nelse:\n    excellent = 0\n    for student in data:\n        grades = student[1:]\n        if grades and all(g == 5 for g in grades):\n            excellent += 1\n        elif len(student) == 2 and student[1] == 5:\n            # на случай формата ["Павел", 5]\n            excellent += 1\n\n    ans = excellent / len(data)\n    # чтобы совпасть с ожидаемыми "0.333", "0.667" и т.п.\n    out = f"{ans:.3f}".rstrip("0").rstrip(".")\n    if "." not in out:\n        out += ".0"\n    print(out)\n	python	accepted	0.05446000000000001	\N	50	50	130		2026-01-14 19:12:44.702221
41	1	1	import ast\nimport sys\n\n# Читаем данные\ndata = ast.literal_eval(sys.stdin.read())\n\n# Считаем отличников\nexcellent = sum(1 for student in data if all(grade == 5 for grade in student[1:]))\n\n# Выводим результат\nprint(excellent / len(data) if data else 0.0)	python	partially_correct	0.05018000000000001	\N	48	50	124		2026-01-14 19:13:10.000889
42	1	1	def main():\n        # Введите ваш код здесь\n        n = int(input())\n        print(n * 2)\n\n    if __name__ == "__main__":\n        main()	python	runtime_error	0.08022	\N	0	50	0	File "C:\\Users\\E67B~1\\AppData\\Local\\Temp\\tmp8gbx67z8.py", line 6\r\n    if __name__ == "__main__":\r\n                              ^\r\nIndentationError: unindent does not match any outer indentation level	2026-01-19 14:39:25.302012
43	1	6	def main():\n        # Введите ваш код здесь\n        n = int(input())\n        print(n * 2)\n\n    if __name__ == "__main__":\n        main()	python	runtime_error	0.0895666666666667	\N	0	30	0	File "C:\\Users\\E67B~1\\AppData\\Local\\Temp\\tmpit8t7on8.py", line 6\r\n    if __name__ == "__main__":\r\n                              ^\r\nIndentationError: unindent does not match any outer indentation level	2026-01-19 21:38:02.631645
44	1	6	nums = map(int, input().split())\n\nresult = []\nfor n in nums:\n    if n % 2 == 0:\n        result.append("четное")\n    else:\n        result.append("нечетное")\n\nprint(" ".join(result))\n	python	accepted	0.060966666666666676	\N	30	30	22		2026-01-19 21:40:49.53988
45	7	6	import sys\n\ndata = sys.stdin.read().split()\nresult = []\n\nfor x in data:\n    n = int(x)\n    result.append("четное" if n % 2 == 0 else "нечетное")\n\nprint(" ".join(result))\n	python	accepted	0.05966666666666666	\N	30	30	20		2026-01-19 21:53:07.714666
46	7	1	import ast\nimport sys\n\ndata = ast.literal_eval(sys.stdin.read().strip())\n\ntotal_students = len(data)\nexcellent = 0\n\nfor student in data:\n    grades = student[1:]  # все элементы кроме имени\n    if grades and all(grade == 5 for grade in grades):\n        excellent += 1\n\n# доля отличников\nresult = excellent / total_students if total_students > 0 else 0\n\nprint(result)\n	python	partially_correct	0.07616	\N	47	50	10		2026-01-19 22:11:20.669541
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
\.


--
-- Data for Name: match_results; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.match_results (id, match_id, user_id, attempt_id, score, tests_passed, total_tests, execution_time, submitted_at) FROM stdin;
1	18	7	45	20	30	30	0.05966666666666666	2026-01-19 21:53:09.665673
2	19	7	46	10	47	50	0.07616	2026-01-19 22:11:24.619919
3	20	1	49	79	24	25	0.05848000000000002	2026-01-19 23:02:03.241738
4	24	1	50	80	29	29	0	2026-01-20 11:06:23.702177
5	24	7	51	0	0	29	0	2026-01-20 11:06:23.71443
6	25	1	52	50	30	30	0	2026-01-20 11:10:34.504536
7	25	7	53	0	0	30	0	2026-01-20 11:10:34.509241
8	26	1	54	20	30	30	0	2026-01-27 12:21:41.634846
9	26	7	55	0	0	30	0	2026-01-27 12:21:41.667278
10	28	9	56	20	32	32	0	2026-02-01 22:27:05.652162
11	28	7	57	0	0	32	0	2026-02-01 22:27:05.664261
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
19	1	7	1	loss	-23	23	0	2026-01-19 22:10:09.825534	2026-01-19 22:10:09.869173	2026-01-20 01:10:09.869173	2026-01-19 22:11:24.629943
26	1	7	23	win	11	-11	0	2026-01-27 12:17:50.622476	2026-01-27 12:17:50.651796	2026-01-27 15:17:50.651796	2026-01-27 12:21:41.67547
23	1	7	20	loss	-20	0	0	2026-01-20 10:56:27.324345	2026-01-20 10:56:27.336658	2026-01-20 13:56:27.336658	2026-01-20 10:56:33.783333
25	1	7	7	win	11	-11	0	2026-01-20 11:10:23.366537	2026-01-20 11:10:23.369292	2026-01-20 14:10:23.369292	2026-01-20 11:10:34.512525
28	7	9	21	loss	-17	17	0	2026-02-01 22:26:56.541474	2026-02-01 22:26:56.554055	2026-02-02 01:26:56.554055	2026-02-01 22:27:05.646645
\.


--
-- Data for Name: matchmaking_queue; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.matchmaking_queue (id, user_id, elo, task_id, difficulty, joined_at, last_ping, status) FROM stdin;
91	1	1157	\N	easy	2026-01-27 12:21:47.813196	2026-01-27 12:21:47.877395	matched
80	7	1000	\N	any	2026-01-19 14:49:10.761407	2026-01-19 14:49:14.071839	matched
93	9	1000	\N	easy	2026-02-01 22:26:51.405606	2026-02-01 22:26:54.441576	matched
47	5	1000	4	easy	2026-01-15 08:52:45.383362	2026-01-15 08:52:45.383378	matched
48	1	1210	1	medium	2026-01-15 09:02:51.450064	2026-01-15 09:02:51.45007	matched
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
1	Отличники	Дан набор данных студентов с результатами экзаменов. Определить долю отличников.	Список списков, где каждый внутренний список содержит имя студента (строка) и его оценки (целые числа).	Вывести долю отличников среди всех учеников.	легкая	10	1	256	2025-11-12 20:58:47.723898	[["Иван", 1, 2, 1, 3], ["Юлия", 5, 5, 5, 5]]	0.5	medium	f
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
1	1	[["Иван", 5, 5, 5, 5]]	1.0	t	1
2	1	[["Мария", 4, 4, 4, 4]]	0.0	t	1
3	1	[]	0.0	t	1
4	1	[["Павел", 5]]	1.0	t	1
5	1	[["Оксана", 4]]	0.0	t	1
6	1	[["Анна", 5, 5, 5, 5], ["Борис", 4, 4, 4, 4]]	0.5	t	2
7	1	[["Петр", 5, 5, 5, 5], ["Ольга", 5, 5, 5, 5]]	1.0	t	2
8	1	[["Сергей", 4, 4, 4, 4], ["Дарья", 4, 4, 4, 4]]	0.0	t	2
9	1	[["Константин", 5, 4, 5, 5]]	0.0	t	2
10	1	[["Виктория", 5, 5, 5, 4]]	0.0	t	2
11	1	[["Андрей", 5, 5, 5, 5, 5]]	1.0	t	2
12	1	[["Светлана", 5, 5, 5, 5, 4]]	0.0	t	2
13	1	[["Юрий", 5], ["Ярослав", 4]]	0.5	t	2
14	1	[["Семен", 5, 5, 5], ["Томара", 5, 5, 5]]	1.0	t	2
15	1	[["Филипп", 5, 5], ["Христина", 5, 5]]	1.0	t	2
16	1	[["Алексей", 5, 5, 5, 5], ["Елена", 4, 4, 4, 4], ["Михаил", 3, 3, 3, 3]]	0.333	t	3
17	1	[["Ирина", 5, 5, 5, 5], ["Владимир", 5, 5, 5, 5], ["Наталья", 5, 5, 5, 5]]	1.0	t	3
18	1	[["Александр", 5, 5, 5, 5], ["Маргарита", 4, 5, 4, 5], ["Георгий", 5, 5, 5, 5]]	0.667	t	3
19	1	[["Вадим", 5, 5, 5, 5], ["Людмила", 5, 5, 5, 5], ["Станислав", 4, 4, 4, 4], ["Алина", 3, 3, 3, 3]]	0.5	t	3
20	1	[["Кирилл", 5, 5, 5, 5], ["Лариса", 4, 4, 4, 4], ["Максим", 5, 5, 5, 5], ["Ника", 4, 4, 4, 4]]	0.5	t	3
21	1	[["Олег", 5, 5, 5, 5], ["Полина", 5, 5, 5, 5], ["Руслан", 5, 5, 5, 5], ["София", 4, 4, 4, 4]]	0.75	t	3
22	1	[["Тимофей", 5, 5, 5, 5], ["Ульяна", 4, 4, 4, 4], ["Федор", 3, 3, 3, 3], ["Элина", 2, 2, 2, 2]]	0.25	t	3
23	1	[["Марина", 5, 5, 5, 5], ["Николай", 4, 4, 4, 4], ["Олеся", 3, 3, 3, 3], ["Прохор", 2, 2, 2, 2], ["Раиса", 1, 1, 1, 1]]	0.2	t	3
24	1	[["Модест", 5, 5, 5, 5], ["Нелли", 5, 5, 5, 5], ["Ольгерд", 5, 5, 5, 5], ["Пелагея", 5, 5, 5, 4], ["Регина", 5, 5, 4, 4]]	0.6	t	3
25	1	[["Адам", 5, 5, 5, 5], ["Берта", 5, 5, 5, 5], ["Василиса", 4, 4, 4, 4], ["Гертруда", 4, 4, 4, 4], ["Демьян", 5, 5, 5, 5]]	0.6	t	3
26	1	[["Еремей", 5, 5, 5, 5], ["Жозефина", 5, 5, 5, 5], ["Зиновий", 5, 5, 5, 5], ["Изабелла", 4, 4, 4, 4], ["Корней", 4, 4, 4, 4]]	0.6	t	3
27	1	[["Любовь", 5, 5, 5, 5], ["Матвей", 5, 5, 5, 5], ["Нонна", 5, 5, 5, 5], ["Осип", 5, 5, 5, 5], ["Прасковья", 5, 5, 5, 4]]	0.8	t	3
28	1	[["Альберт", 5, 5, 5, 5], ["Богдана", 4, 4, 4, 4], ["Всеволод", 3, 3, 3, 3], ["Глафира", 2, 2, 2, 2], ["Денис", 1, 1, 1, 1]]	0.2	t	3
29	1	[["Евграф", 5, 5, 5, 5], ["Злата", 5, 5, 5, 5], ["Иосиф", 5, 5, 5, 5], ["Кира", 4, 4, 4, 4], ["Люциан", 4, 4, 4, 4]]	0.6	t	3
30	1	[["Богдан", 5, 5, 5, 5], ["Валерия", 5, 5, 5, 5], ["Григорий", 5, 5, 5, 5], ["Диана", 5, 5, 5, 5]]	1.0	t	3
31	1	[["Евгений", 4, 4, 4, 4], ["Жанна", 4, 4, 4, 4], ["Захар", 4, 4, 4, 4], ["Инна", 4, 4, 4, 4]]	0.0	t	3
32	1	[["Яна", 5, 5, 5, 5], ["Аркадий", 5, 5, 5, 5], ["Белла", 5, 5, 5, 5], ["Вениамин", 5, 5, 5, 5], ["Галина", 4, 4, 4, 4]]	0.8	t	3
33	1	[["Даниил", 5, 5, 5, 5], ["Евдокия", 4, 4, 4, 4], ["Игнат", 5, 5, 5, 5], ["Клавдия", 4, 4, 4, 4], ["Леонид", 5, 5, 5, 5]]	0.6	t	3
34	1	[["Ростислав", 5, 5, 5, 5], ["Степанида", 5, 5, 5, 5], ["Трофим", 5, 5, 5, 5], ["Феврония", 5, 5, 5, 5], ["Эраст", 5, 5, 5, 5]]	1.0	t	3
35	1	[["Мирон", 5, 5, 5, 5], ["Нина", 5, 5, 5, 5], ["Одарка", 5, 5, 5, 5], ["Пантелей", 5, 5, 5, 5], ["Розалия", 5, 5, 5, 5]]	1.0	t	3
36	1	[["Чеслав", 4, 4, 4, 4], ["Шура", 4, 4, 4, 4], ["Эмма", 4, 4, 4, 4], ["Юлиан", 4, 4, 4, 4], ["Яков", 4, 4, 4, 4]]	0.0	t	3
37	1	[["Дмитрий", 3, 3, 3, 3]]	0.0	t	3
38	1	[["Екатерина", 2, 2, 2, 2]]	0.0	t	3
39	1	[["Артем", 1, 1, 1, 1]]	0.0	t	3
40	1	[["Юлия", 5, 5, 5, 5, 5, 5]]	1.0	t	3
41	1	[["Роман", 5, 5, 5, 5, 3]]	0.0	t	3
42	1	[["Татьяна", 5, 5, 5, 5, 5, 4]]	0.0	t	3
43	1	[["Цветана", 5, 5, 5, 5, 5, 5, 5]]	1.0	t	3
44	1	[["Эдуард", 5, 5, 4]]	0.0	t	3
45	1	[["Агата", 5, 5, 5, 5, 5, 5], ["Бронислав", 5, 5, 5, 5, 5, 4]]	0.5	t	3
46	1	[["Варвара", 5, 5], ["Геннадий", 5, 4]]	0.5	t	3
47	1	[["Дорофей", 5, 5, 5, 5], ["Ефросинья", 5, 5, 5, 4]]	0.5	t	3
48	1	[["Зоя", 5, 5, 5], ["Ипполит", 5, 5, 4]]	0.5	t	3
49	1	[["Капитолина", 5], ["Лев", 4]]	0.5	t	3
50	1	[["Савва", 5, 5, 5, 5], ["Тереза", 5, 5, 5, 5], ["Устинья", 5, 5, 5, 5], ["Фаина", 5, 5, 5, 5], ["Харитон", 5, 5, 5, 5]]	1.0	t	3
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

COPY public.users (id, username, email, password_hash, created_at, elo, best_elo, wins, losses, games_played, title, draws, is_online, last_seen) FROM stdin;
2	MISTIK	e.kraeva@bda.com	$2b$12$d57eqQf9CNb/..eImZ7R4O9dBPNa.qOp9DElweBmQAJ6kaqdOvDzS	2025-11-04 19:02:16.162693	1000	1000	0	0	0	Новичок	0	f	2025-12-22 13:41:12.489756
3	kkkkk	ktyf79@mail.ru	$2b$12$2DXmrzoHBtXgmSoa4SjUaeFcOO8PWeRoPjBartX1O49/4l0FeVWta	2025-11-05 23:46:15.407721	1000	1000	0	0	0	Новичок	0	f	2025-12-22 13:41:12.489756
4	jsgjwg	ovesik07-0775@mail.ru	$2b$12$zQYDrOtYStgdtXMx3Suo7eKaMYJp1W1Br5GseX6ZvRuIfIMT4FGA.	2026-01-15 08:51:16.850329	1000	1000	0	0	0	Новичок	0	f	2026-01-15 08:51:17.355697
7	kkkk	k@mail.ru	$2b$12$kKrlyGummvB3hRGozZMINeVRJVcFS.1Ckwv9nolxGIw851m3/bjcy	2026-01-19 12:37:37.314075	995	1059	5	6	12	Новичок	1	f	2026-02-01 22:27:05.640986
5	dnfefjh	leradavidova111@yandex.com	$2b$12$xj2jEEord8IRd1.uBLadiuzKp3ePfGUVN.MWZNOCb4vEJFO2ut78O	2026-01-15 08:52:22.79635	1000	1000	0	0	0	Новичок	0	f	2026-01-15 10:33:16.309086
9	oooooo	1@mail.ru	$2b$12$TjQD9F4v5jz83nat3/tZwegB3ocFJv6cjbD3lv05oL55CGklL35Jm	2026-02-01 22:26:37.947734	1017	1017	1	0	1	Новичок	0	f	2026-02-01 22:27:08.438019
6	popa	egor@gmail.com	$2b$12$fDdxlX7u4qKGCyg6jrChtuH3AzCWemltoGIBxk7fsEwSn7pbAjdg6	2026-01-15 10:33:08.34786	1000	1000	0	0	0	Новичок	0	f	2026-01-15 11:02:21.537714
8	mmmkkk	e@mail.ru	$2b$12$gmVFHUuNNEWvTiX/uXfsZeleGwcbUeE3yR3BoIx3eQuSLtTmIRaZ2	2026-02-01 22:25:38.913862	1000	1000	0	0	0	Новичок	0	f	2026-02-01 22:25:39.154518
1	mistik	guzarevicvlad47@mail.ru	$2b$12$Vj0H6uUD8r6ldUx1tiy.HeGCcsrLDAzT6CdlS7tV.QCGPA7GkhXk.	2025-11-04 18:40:37.778167	1151	2200	74	57	134	Мастер алгоритмов	1	f	2026-01-28 22:45:49.784761
\.


--
-- Name: attempts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.attempts_id_seq', 57, true);


--
-- Name: match_results_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.match_results_id_seq', 11, true);


--
-- Name: matches_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.matches_id_seq', 28, true);


--
-- Name: matchmaking_queue_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.matchmaking_queue_id_seq', 93, true);


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

SELECT pg_catalog.setval('public.users_id_seq', 9, true);


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
-- Name: idx_matches_played_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_matches_played_at ON public.matches USING btree (played_at);


--
-- Name: idx_matches_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_matches_user_id ON public.matches USING btree (user_id);


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
-- PostgreSQL database dump complete
--

\unrestrict kyy4fADw0xa8hYKNqfKtfJqx320KnrvFGdWdrb9q0L0j0cnUXkFZDhbJ2yy30v0

