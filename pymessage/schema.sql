drop table if exists user;
create table user (
    id integer primary key autoincrement,
    username text not null,
    lastread integer
);

drop table if exists messages;
create table messages (
    id integer primary key autoincrement,
    userId integer not null,
    message text not null,
    foreign key(userId) references user(id)
);

