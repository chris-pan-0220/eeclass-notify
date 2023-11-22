from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
# import datetime
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

db_url = config['credential']['DB_URL']
Base = declarative_base()

class Course(Base):
    __tablename__ = 'course'

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, nullable=False) 
    title = Column(String, nullable=False)
    
    def __repr__(self):
        return f"<Course(course_id='{self.course_id}, name='{self.title}')>"

# 定义Homework模型
class Homework(Base):
    __tablename__ = 'homework'

    id = Column(Integer, primary_key=True)
    # course_id = Column(Integer, ForeignKey('course.id'))
    course_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    deadline = Column(DateTime, nullable=False)
    is_finish = Column(Boolean, nullable=False)

    def __repr__(self):
        return f"<Homework(title='{self.title}', deadline='{self.deadline}', is_finish='{self.is_finish}', course_id={self.course_id}')>"
    
# migration
def migration():
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

# class HomeworkDB:
#     def __init__(self, Session) -> None:
#         self.Session = Session
    
#     def add(self, title: str, deadline: datetime, is_finish: bool):
#         session = self.Session()
#         new_homework = Homework(title=title, deadline=deadline, is_finish=is_finish)
#         session.add(new_homework)
#         session.commit()
#         session.close()

#     def all(self) -> list:
#         session = self.Session()
#         homework_list = session.query(Homework).all()
#         session.close()
#         return homework_list
    
#     def delete(self, id: int):
#         session = self.Session()
#         homework_to_delete = session.query(Homework).filter(Homework.id == id).first()
#         if homework_to_delete:
#             session.delete(homework_to_delete)
#             session.commit()
#         session.close()





# 以下僅為測試

# 创建Session类
# Session = sessionmaker(bind=engine)

# 示例：添加新作业
# def add_homework(title, deadline):
#     session = Session()
#     new_homework = Homework(title=title, deadline=deadline)
#     session.add(new_homework)
#     session.commit()
#     session.close()

# # 示例：查询所有作业
# def query_all_homework():
#     session = Session()
#     homework_list = session.query(Homework).all()
#     session.close()
#     return homework_list

# # 示例：删除作业
# def delete_homework(homework_id):
#     session = Session()
#     homework_to_delete = session.query(Homework).filter(Homework.id == homework_id).first()
#     if homework_to_delete:
#         session.delete(homework_to_delete)
#         session.commit()
#     session.close()

# 需要的op 
"""
add homework (course_id, title, deadline, finish)
get homework by a class
    check id 是否跟資料庫當中的內容一致title
update homework by a class
過期刪除作業
"""
# test db 
if __name__ == '__main__':
    # migration()
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    # homeworkDB = HomeworkDB(Session)

    # title = '測試作業'
    # deadline = datetime.datetime.today()
    # is_finish = False

    # print(f'新增作業: {title}, {deadline}, {is_finish}')
    # homeworkDB.add(title, deadline, is_finish)
    # homeworkDB.add(title, deadline, is_finish)

    # print('所有作業: ')
    # homeworkList = homeworkDB.all()
    # for h in homeworkList:
    #     print(h)
    #     print(f'id: {h.id}')
    #     print(f'title: {h.title}')
    #     print(f'deadline: {h.deadline}')
    #     print(f'is_finish: {h.is_finish}')
        

    # print('刪除作業: ')
    # homeworkDB.delete(1)
    # homeworkDB.delete(2)
    homework = session.query(Homework).filter(Homework.is_finish == True).all()
    for h in homework: 
        print(h)
    
"""
初始化db
新增course
新增尚未到期的作業

# 蒐集course_number
# 蒐集課程公告: get data from db


增資
私募
"""